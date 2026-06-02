"""Generate Harbor task directories for the ct_abnormality benchmark.

Reads the canonical 10-volume manifest at
``scripts/ct_abnormality/assets/manifest.yaml`` (volume IDs only — no gold, no
report text) and produces one task tree per volume under
``tasks/ct_abnormality/<volume_stem>/``. Each tree contains:

- ``task.toml`` — Harbor task config.
- ``instruction.md`` — agent-facing prompt.
- ``environment/Dockerfile`` — Python 3.12 base with viewing/imaging libs preinstalled.
- ``environment/docker-compose.yaml`` — two services: a one-shot ``bootstrap``
  that downloads + stages the volume and derives the gold, and ``main`` that
  ``depends_on: bootstrap: condition: service_completed_successfully``. They
  share ``/workspace/data`` via a named compose volume so main sees the staged
  volume as soon as bootstrap exits cleanly. Pattern follows medagentbench.
- ``environment/bootstrap.sh`` — runs in the bootstrap service: downloads the
  volume + the paired radiology report from Hugging Face on cache miss, then
  runs ``gold_derivation.py`` to derive this volume's gold from the report and
  write ``/tests/gold.json`` (gitignored) and ``/workspace/data/labels.txt``.
- ``environment/gold_derivation.py`` — copy of
  ``scripts/ct_abnormality/gold_derivation.py`` (the phrase rules), used by the
  bootstrap to derive gold at runtime.
- ``tests/harbor_evaluator.py`` — copy of ``scripts/ct_abnormality/harbor_evaluator.py``.
- ``tests/verify.py`` and ``tests/test.sh`` — Harbor verifier entry points.

Gold is intentionally **not** generated here and **not** committed: it is
derived in-container at run time so the gated CT-RATE reports / answer key are
never redistributed in git. ``tests/gold.json`` is gitignored.

Usage:

    uv run python scripts/ct_abnormality/generate_harbor_tasks.py
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts" / "ct_abnormality"
ASSETS_DIR = SCRIPTS_DIR / "assets"
MANIFEST_PATH = ASSETS_DIR / "manifest.yaml"
TASKS_ROOT = REPO_ROOT / "tasks" / "ct_abnormality"

PYTHON_BASE = "3.12-slim"
PIP_PINS = "nibabel==5.4.2 pillow==10.4.0 huggingface_hub==0.27.0 numpy==2.3.4 pyyaml==6.0.2"


def build_task_toml(task_id: str) -> str:
    return f"""version = "1.0"

[metadata]
benchmark = "ct_abnormality"
mode = "etl-task"
task_id = "{task_id}"
submission_path = "/workspace/submission/predictions.txt"

[verifier]
timeout_sec = 300.0

[agent]
timeout_sec = 3600.0

[environment]
build_timeout_sec = 1800.0
allow_internet = true
cpus = 2
memory_mb = 8192
storage_mb = 8192
gpus = 0
mcp_servers = []

[verifier.env]

[solution.env]
"""


INSTRUCTION_TEMPLATE = """# Chest CT Multi-Abnormality Classification

You are working inside an environment that contains a single non-contrast
chest-CT volume and a list of clinical findings to evaluate. **For each
listed finding, decide whether the finding is present or absent in the
scan, and write your prediction.**

## Inputs

- `/workspace/data/scan.nii.gz` — the chest CT volume (NIfTI format,
  axial slices, intensities in Hounsfield Units roughly -1024 to +3000).
  In-plane resolution and slice count vary by scan; voxel size is in the
  NIfTI header.
- `/workspace/data/labels.txt` — the clinical labels you must evaluate,
  one per line. Only these labels will be scored. The list is short
  (typically 4 to 12 labels) and is volume-specific.

## Output

Write a plain text file at `/workspace/submission/predictions.txt`
containing one `<label>: yes` or `<label>: no` line per requested label.
Use the exact label name from `labels.txt` (case-insensitive). Order
does not matter; the verifier matches by label name.

Format example:

    Cardiomegaly: no
    Pleural effusion: yes
    Lung nodule: no
    # comments and blank lines are ignored

## Rules

- The container has internet access. You are free to install whatever
  Python libraries, system packages, or tools you decide you need to
  inspect the volume and decide each label. How to actually look at a
  3-D NIfTI volume is up to you to figure out.
- Solve the task using only the volume on disk. Do not try to look up
  the dataset's published labels or report on the internet.
- The reward is **binary** — you must get **every** requested label
  correct to score `1.0`. A single mistake yields `0.0`. Diagnostic
  per-label and per-disease F1 are reported alongside but do not affect
  the per-task reward.
- **You have up to 1 hour to complete this task.**
"""


DOCKERFILE_TEMPLATE = f"""FROM python:{PYTHON_BASE}

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash ca-certificates curl util-linux \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir {PIP_PINS}

# Don't write .pyc files anywhere -- keeps the bind-mounted /tests dir free of
# root-owned __pycache__ residue that the host can't delete.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# No COPY of environment/workspace/: that directory is intentionally empty
# for ct_abnormality (the bootstrap service populates /workspace/data/
# via a named compose volume at runtime), and Docker BuildKit refuses to
# COPY an empty directory ("failed to compute cache key").
COPY environment/bootstrap.sh /bootstrap.sh
# Phrase-rule gold derivation, run by the bootstrap at runtime to build
# /tests/gold.json from the downloaded report.
COPY environment/gold_derivation.py /opt/gold_derivation.py
RUN chmod +x /bootstrap.sh \\
    && mkdir -p /workspace/submission /workspace/data

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive. The bootstrap
# service uses an explicit ``command:`` in docker-compose.yaml to run
# /bootstrap.sh and exit cleanly.
"""


def build_docker_compose() -> str:
    """Per-task docker-compose with a one-shot bootstrap service that the main
    service depends on via ``condition: service_completed_successfully``.

    Pattern follows ``tasks/medagentbench/environment/docker-compose.yaml``:
    a sibling service does the prep work and Compose waits for it to exit
    cleanly before bringing main up. Harbor invokes
    ``docker compose up --detach --wait`` which respects this condition,
    so by the time Harbor execs the agent into main the data is already
    staged at ``/workspace/data/scan.nii.gz`` and ``labels.txt``.

    The bootstrap and main containers share ``/workspace/data`` through a
    named compose volume (per-task, scoped to the compose project) so the
    bootstrap's downloads + label list become visible to main without any
    runtime sentinel files in /workspace/.

    The bootstrap also bind-mounts the per-task ``tests/`` dir read-write so it
    can write the runtime-derived ``gold.json`` there (gitignored); Harbor
    mounts that same host dir as ``/tests`` when it later runs the verifier.
    ``main`` never mounts ``tests/`` — the agent has no path to the gold.

    Portability: every host path is **relative to this compose file's
    location** (``tasks/ct_abnormality/<task>/environment/``) so the repo
    runs unchanged on any machine — no absolute host paths are baked in at
    generation time. The Hugging Face credential is supplied via
    ``env_file: ../../../../.env`` (``HF_TOKEN``) so the user never has to
    ``export`` anything before invoking Harbor, mirroring
    ``tasks/xray_report_correction/`` and ``tasks/ehrshot/``. The token is
    given to ``bootstrap`` only — ``main`` (where the agent runs) never sees
    it, so the download credential cannot leak to the agent.
    """
    # Only `main` carries a `build:` directive; `bootstrap` references the
    # same image by tag. This is important: when two compose services build
    # against the same context concurrently, BuildKit's local-context loader
    # races and one of the services receives a 2-byte (empty) context,
    # making subsequent COPY steps fail with "failed to compute cache key".
    # By centralizing the build on `main` and tagging the result, bootstrap
    # gets a fully-realized image after the single build phase.
    #
    # ../../../../ walks environment/ -> <task>/ -> ct_abnormality/ -> tasks/
    # -> repo root, so the cache lives at
    # <repo_root>/scripts/ct_abnormality/assets/raw_cache (gitignored).
    return """services:
  main:
    build:
      context: ..
      dockerfile: environment/Dockerfile
    image: ${COMPOSE_PROJECT_NAME}-img
    volumes:
      - workspace-data:/workspace/data
    depends_on:
      bootstrap:
        condition: service_completed_successfully
    environment:
      - PYTHONUNBUFFERED=1

  bootstrap:
    image: ${COMPOSE_PROJECT_NAME}-img
    env_file:
      # HF_TOKEN (CT-RATE is OpenRAIL-gated) lives here. Other vars in .env
      # are loaded harmlessly. Only bootstrap reads .env, so the token never
      # reaches main / the agent.
      - ../../../../.env
    volumes:
      # Repo-relative shared NIfTI + report cache (RW so bootstrap can populate
      # on a cache miss). Resolves to <repo_root>/scripts/ct_abnormality/assets/raw_cache.
      - ../../../../scripts/ct_abnormality/assets/raw_cache:/data/_cache:rw
      # Per-task tests/ dir, RW: bootstrap writes the runtime-derived gold.json
      # here (gitignored). Harbor mounts the same host dir as /tests for the
      # verifier. main does NOT mount this — the agent never sees the gold.
      - ../tests:/tests:rw
      - workspace-data:/workspace/data
    command: ["/bin/bash", "/bootstrap.sh"]

volumes:
  workspace-data:
"""


BOOTSTRAP_SH = r"""#!/bin/bash
# One-shot bootstrap container for the ct_abnormality benchmark. Compose
# starts this service, waits for it to exit cleanly, and only then brings
# the main service up (via depends_on: condition: service_completed_successfully).
#
# Responsibilities:
#   1. If /data/_cache/<volume>.nii.gz is missing, download it from Hugging
#      Face (CT-RATE; OpenRAIL-gated; needs HF_TOKEN, supplied via the
#      env_file: ../../../../.env entry in docker-compose.yaml). Freeze it
#      read-only. The whole fetch runs under a global flock so concurrent
#      task bootstraps don't hammer the CDN for the same file.
#   2. Download the validation reports CSV into the same cache (once, shared).
#   3. Derive THIS volume's gold from its report via /opt/gold_derivation.py
#      (the committed phrase rules) and write:
#         - /tests/gold.json          (verifier-only; gitignored on the host)
#         - /workspace/data/labels.txt (agent-visible label list, names only)
#      Gold is never committed to git — it is reconstructed here at run time.
#   4. Copy the volume to /workspace/data/scan.nii.gz so main sees it via the
#      shared workspace-data named volume.
#
# When this script exits 0, Compose lets main start.
set -euo pipefail

CACHE=/data/_cache
GLOBAL_LOCK="$CACHE/.bootstrap.lock"
VOLUME_NAME="__VOLUME_NAME__"
HF_REPO="__HF_REPO__"
HF_PATH="__HF_PATH__"
HF_REPORTS_PATH="__HF_REPORTS_PATH__"
SRC="$CACHE/$VOLUME_NAME"
REPORTS_CSV="$CACHE/$(basename "$HF_REPORTS_PATH")"
DST=/workspace/data/scan.nii.gz

mkdir -p /workspace/data /tests "$CACHE"

_require_token() {
    if [ -z "${HF_TOKEN:-}" ]; then
        echo "[bootstrap] no Hugging Face token: HF_TOKEN is empty." 1>&2
        echo "  Accept the access agreement at https://huggingface.co/datasets/ibrahimhamamci/CT-RATE" 1>&2
        echo "  and add HF_TOKEN=hf_... to the repo-root .env file." 1>&2
        exit 2
    fi
}

# Download an HF dataset file into $CACHE/<basename> on cache miss.
_download() {
    local hf_path="$1" dest="$2"
    if [ -f "$dest" ] && [ -s "$dest" ]; then
        echo "[bootstrap] cache hit: $dest"
        return
    fi
    _require_token
    echo "[bootstrap] downloading $hf_path ..."
    HF_PATH="$hf_path" DEST="$dest" python3 - <<'PYEOF'
import os, shutil
from pathlib import Path
from huggingface_hub import hf_hub_download
token = os.environ["HF_TOKEN"].strip()
local = hf_hub_download(
    repo_id=os.environ["HF_REPO"],
    filename=os.environ["HF_PATH"],
    repo_type="dataset",
    token=token,
    local_dir=os.environ["CACHE"] + "/.hf_staging",
)
dest = Path(os.environ["DEST"])
if dest.exists() or dest.is_symlink():
    dest.unlink()
shutil.copyfile(local, dest)
PYEOF
    chmod a-w "$dest" 2>/dev/null || true
}

# Serialize cold downloads across concurrent task containers. chmod runs inside
# the critical section so files are frozen before another container races them.
export HF_REPO CACHE
exec 9>"$GLOBAL_LOCK"
flock 9
_download "$HF_PATH" "$SRC"
_download "$HF_REPORTS_PATH" "$REPORTS_CSV"
flock -u 9

# Derive this volume's gold from its report and stage the agent label list.
# Writes /tests/gold.json (gitignored host file) + /workspace/data/labels.txt.
python3 /opt/gold_derivation.py \
    --reports-csv "$REPORTS_CSV" \
    --volume "$VOLUME_NAME" \
    --out-gold /tests/gold.json \
    --out-labels /workspace/data/labels.txt

# Stage volume into the workspace-data named volume that main shares.
cp "$SRC" "$DST"

echo "[bootstrap] done — main can start"
"""


TEST_SH = """#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p /logs/verifier /logs/artifacts
python verify.py
"""


VERIFY_PY = """#!/usr/bin/env python3
\"\"\"Per-task verifier entry point. Calls harbor_evaluator.evaluate.\"\"\"

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harbor_evaluator import evaluate  # noqa: E402


def main() -> None:
    submission = Path("/workspace/submission/predictions.txt")
    gold = Path(__file__).resolve().parent / "gold.json"
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, gold, log_dir)
    print(f"reward={score:.6f}")


if __name__ == "__main__":
    main()
"""


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _ensure_clean(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _hf_path_for(volume_name: str, hf_split_root: str) -> str:
    stem = volume_name[: -len(".nii.gz")]
    parts = stem.split("_")
    patient = "_".join(parts[:2])
    study = "_".join(parts[:3])
    return f"{hf_split_root}/{patient}/{study}/{volume_name}"


def _build_bootstrap(volume_name: str, hf_repo: str, hf_path: str, hf_reports_path: str) -> str:
    return (
        BOOTSTRAP_SH
        .replace("__VOLUME_NAME__", volume_name)
        .replace("__HF_REPO__", hf_repo)
        .replace("__HF_PATH__", hf_path)
        .replace("__HF_REPORTS_PATH__", hf_reports_path)
    )


def _task_id_for(volume_name: str) -> str:
    """Derive the canonical task_id from a CT-RATE volume filename.

    Hardcoded convention: the task_id IS the volume stem (no ``.nii.gz``),
    e.g. ``valid_670_a_1.nii.gz`` -> ``valid_670_a_1``. This makes per-task
    directories under ``tasks/ct_abnormality/`` self-identifying with the
    upstream CT-RATE validation ID, so a human looking at a run can refer
    back to the original scan and report.

    The agent never sees this name inside ``/workspace/``: the volume is
    bind-mounted to ``/workspace/data/scan.nii.gz`` and the labels file
    contains only the label list. The container hostname (set by
    docker-compose) does include the task_id, so an adversarial agent
    that runs ``hostname`` can recover the volume identifier — that is a
    knowingly accepted trade-off for host-side traceability.
    """
    if not volume_name.endswith(".nii.gz"):
        raise ValueError(f"Unexpected volume filename: {volume_name!r}")
    return volume_name[: -len(".nii.gz")]


def _build_task(
    task_root: Path,
    entry: dict,
    manifest: dict,
) -> None:
    _ensure_clean(task_root)
    volume_name = entry["volume_name"]
    task_id = _task_id_for(volume_name)

    _write(task_root / "task.toml", build_task_toml(task_id))
    _write(task_root / "instruction.md", INSTRUCTION_TEMPLATE)

    env_dir = task_root / "environment"
    workspace = env_dir / "workspace"
    tests_dir = task_root / "tests"
    workspace.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    _write(env_dir / "Dockerfile", DOCKERFILE_TEMPLATE)
    _write(env_dir / "docker-compose.yaml", build_docker_compose())

    hf_path = _hf_path_for(volume_name, manifest["hf_split_root"])
    bootstrap = _build_bootstrap(
        volume_name, manifest["hf_repo"], hf_path, manifest["hf_reports_path"]
    )
    bootstrap_path = env_dir / "bootstrap.sh"
    _write(bootstrap_path, bootstrap)
    bootstrap_path.chmod(0o755)

    # Ship the phrase-rule module into the image so the bootstrap can derive
    # gold from the report at run time. Gold itself is NOT written here — it is
    # produced in-container (gitignored tests/gold.json) so the answer key /
    # report text are never committed.
    shutil.copyfile(
        SCRIPTS_DIR / "gold_derivation.py",
        env_dir / "gold_derivation.py",
    )

    # Verifier assets (gold.json is created at run time by the bootstrap).
    shutil.copyfile(
        SCRIPTS_DIR / "harbor_evaluator.py",
        tests_dir / "harbor_evaluator.py",
    )
    _write(tests_dir / "verify.py", VERIFY_PY)
    test_sh_path = tests_dir / "test.sh"
    _write(test_sh_path, TEST_SH)
    test_sh_path.chmod(0o755)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--tasks-root", type=Path, default=TASKS_ROOT)
    args = parser.parse_args(argv)

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    args.tasks_root.mkdir(parents=True, exist_ok=True)
    # Ensure a tasks/ct_abnormality/README.md placeholder exists for tasks/README.md links.
    readme = args.tasks_root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# ct_abnormality Harbor tasks\n\n"
            "Generated by `scripts/ct_abnormality/generate_harbor_tasks.py`. "
            "Do not edit by hand.\n"
        )

    for entry in manifest["volumes"]:
        task_id = _task_id_for(entry["volume_name"])
        task_root = args.tasks_root / task_id
        print(f"[generate] {task_id} ({entry['volume_name']}, gold derived at runtime)")
        _build_task(task_root, entry, manifest)

    return 0


if __name__ == "__main__":
    sys.exit(main())
