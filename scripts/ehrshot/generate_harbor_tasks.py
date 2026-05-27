"""Generate Harbor task subdirectories for the EHRSHOT benchmark.

Single entry point. Running:

    uv run python scripts/ehrshot/generate_harbor_tasks.py

generates 15 task folders under ``tasks/ehrshot/``, each wired up so the
EHRSHOT bundle is downloaded **on the fly when the container starts**
(not at task-generation time). The bootstrap service per task pulls the
bundle from Redivis on cache miss, freezes it RO, and signals main via
``depends_on: condition: service_completed_successfully``. The host cache
directory is shared across all 15 task containers so only the first
container per host pays the download cost.

Per-task layout::

    tasks/ehrshot/<id>/
      task.toml
      instruction.md
      environment/
        Dockerfile
        docker-compose.yaml      # two services: main + bootstrap
        bootstrap.sh             # downloads + freezes the shared cache
      tests/
        harbor_evaluator.py
        verify.py
        test.sh
        baseline.json   # baseline_auroc resolved at verify time
        val_labels.csv  # the hidden labels (verifier-only); written in Milestone 2

Host prerequisites (one-time, per host):
  1. Accept the EHRSHOT data-use agreement at
     https://redivis.com/datasets/53gc-8rhx41kgt
  2. Generate a Redivis API token with read scope on the dataset.
  3. Write the token to ``~/.redivis/api_token`` (or pass ``--token-file``).

The bootstrap container mounts this token RO; the main container does not
see it. The published baseline AUROC for each task is resolved at
**verify time** by reading
``/data/_cache/EHRSHOT_ASSETS/results/<id>/all_results.csv`` (the bundle
is mounted RO in main).

This file is **Milestone 1+5 scaffolding**: the slicing of EHR events into
per-task workspace/data/ is intentionally a stub here and lands fully in
Milestone 2 (`stage_data.py`). The 15 folders are still useful at this
point because Harbor can enumerate them, the task.toml fields are right,
and downstream milestones only have to fill in the workspace/ contents +
verifier wiring.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import statistics
import sys
from pathlib import Path

import yaml

# Local imports — keep them lazy-friendly so ``--help`` works without redivis.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from download import default_assets_dir, main as download_main  # noqa: E402
import stage_data  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts" / "ehrshot"
ASSETS_DIR = SCRIPTS_DIR / "assets"
TASK_CONFIGS = ASSETS_DIR / "task_configs.yaml"
TASKS_ROOT = REPO_ROOT / "tasks" / "ehrshot"


# ---------------------------------------------------------------------------
# Templates (per-task identical except for the substituted task_id and labels)
# ---------------------------------------------------------------------------

TASK_TOML = """version = "1.0"

[metadata]
benchmark = "ehrshot"
mode = "etl-task"
task_id = "{task_id}"
submission_path = "/workspace/submission/predictions.csv"

[verifier]
timeout_sec = 300.0

[agent]
timeout_sec = 3600.0

[environment]
build_timeout_sec = 1800.0
allow_internet = true
cpus = 16
memory_mb = 65536
# Bundle is ~17 GB extracted on the host (bind-mounted RO into bootstrap
# only, doesn't count here). The workspace-data named volume holds this
# task's sliced events.csv (~1-2 GB) plus pretrained model checkpoints,
# scratch features, intermediate parquet, etc. 64 GB leaves headroom for
# HuggingFace caches or large feature pickles.
storage_mb = 65536
# Default to CPU-only since the current host has no nvidia-docker runtime.
# Bump to ``gpus = 1`` when running on a GPU-capable host (Harbor will
# refuse to launch otherwise).
gpus = 0
mcp_servers = []

[verifier.env]

[solution.env]
"""


INSTRUCTION_MD = """# {task_id}

## Overview

This is a **clinical event prediction task** on real electronic health
record (EHR) data. Each prediction row is defined by a **patient** and a
specific **prediction time point**. Your goal is to use the patient's
longitudinal clinical history — every observed event (diagnosis, drug,
lab, procedure, visit) **strictly before** the prediction time — to
predict the value of a target label at that time point. The same pattern
applies to every row: read the patient's past timeline up to a moment,
decide the label at that moment.

## Task

{task_description}

## Label semantics

{label_semantics}

You have access to a **train** split and a **val** split with labels, plus
a longitudinal event log for all patients in those splits. Explore the
data, learn a strategy from train and val, and apply it to a held-out
**test** split provided without labels. Submit a probability for each
test row.

**Push for the strongest predictions you can produce.** You are free to
use any approach. Iterate freely: only the final submission you write to
`predictions.csv` is scored.

## Inputs (under `/workspace/data/`)

- `train_labels.csv` — labels for the train split. Columns:
  `patient_id, prediction_time, label`{multilabel_note}.
- `val_labels.csv` — labels for the val split (same schema as train).
- `test_examples.csv` — `(patient_id, prediction_time)` rows you must
  predict on. **No labels.**
- `events.csv` — longitudinal flat event log for all patients in this
  task's train + val + test cohorts. Columns:
  `patient_id, start, end, code, value, unit, visit_id, omop_table`.
  Each row is one observed clinical event. The format is a single flat
  table (not the canonical OMOP CDM multi-table schema); `omop_table`
  records which OMOP source table the event came from
  (`condition_occurrence`, `drug_exposure`, `measurement`,
  `procedure_occurrence`, `visit_occurrence`, `visit_detail`,
  `observation`, `note`, `device_exposure`, `death`, `person`). The
  `code` field uses standard OMOP vocabularies with a prefix:
  e.g. `SNOMED/...`, `LOINC/...`, `RxNorm/...`, `CVX/...`, `ICD10PCS/...`,
  `CPT4/...`, plus demographic/visit metadata codes like `Gender/F`,
  `Race/...`, `Visit/IP`. `value` is populated for numeric events
  (e.g. lab results) and empty otherwise. The file is read-only and
  large (~1-2 GB after slicing); stream it with
  `pandas.read_csv(..., chunksize=...)` or `pyarrow` if memory is tight.

  **Anti-leakage rule:** when scoring or training a row at
  `prediction_time = T`, only use events with `start < T` for that
  patient. Events at or after `T` are not legitimately observable.

- `splits/person_id_map.csv` — patient → split mapping (so you can
  cross-check which patients are train/val/test).

## Output

Write `/workspace/submission/predictions.csv` with columns:
{submission_columns_block}

Each row should correspond to a row in `test_examples.csv`. Each
probability column is a **continuous value anywhere in `[0, 1]`** (any
real number, not restricted to discrete bins) expressing **how confident
you are that the label is positive (1)**:

  - the closer to **1**, the more confident you are the label is positive,
  - the closer to **0**, the more confident you are the label is negative.

Submit raw continuous probabilities/scores, not hard 0/1 predictions and
not coarse buckets. For multilabel tasks, each label column is independent
(one continuous confidence per finding; they do not need to sum to 1
across columns).

The verifier matches rows by `(patient_id, prediction_time)` and rejects
submissions with missing rows.

## Scoring

Your submission will be scored with **AUROC** (Area Under the Receiver
Operating Characteristic curve) against the held-out test labels. For
multilabel tasks the score is the mean AUROC across the label columns.

## Constraints

- **Time budget: ~1 hour** for the full task.
- You have internet access and may install any Python packages or
  external tools you need.
"""


DOCKERFILE = """FROM python:3.12-slim

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash ca-certificates curl util-linux unzip \\
    && rm -rf /var/lib/apt/lists/*

# Pre-install the standard ML stack so the agent can fit a count+GBM
# baseline (or a FM-embedding-based classifier) without runtime pip.
# ``redivis`` is needed by the bootstrap service to pull the EHRSHOT bundle
# on cache miss; the main service ignores it.
RUN pip install --no-cache-dir \\
    numpy==2.1.3 \\
    pandas==2.2.3 \\
    scipy==1.14.1 \\
    scikit-learn==1.5.2 \\
    lightgbm==4.5.0 \\
    xgboost==2.1.3 \\
    pyarrow==18.1.0 \\
    redivis==0.20.7

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# Slicer + scorer baked into the image. Bootstrap runs stage_data.py to
# populate /workspace/data/ AND /tests/test_labels.csv from the downloaded
# bundle. The trial-side verifier imports evaluate.py to compute AUROC.
COPY environment/bootstrap.sh /bootstrap.sh
COPY environment/stage_data.py /opt/ehrshot/stage_data.py
COPY environment/evaluate.py   /opt/ehrshot/evaluate.py
RUN chmod +x /bootstrap.sh \\
    && mkdir -p /workspace/submission /workspace/data

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity``. The bootstrap service uses an explicit
# ``command:`` in docker-compose.yaml to run /bootstrap.sh and exit cleanly.
"""


# Two-service compose: bootstrap downloads + freezes the shared cache, then
# main starts via ``depends_on: condition: service_completed_successfully``.
# The cache is bind-mounted to the host so it survives across the 15 task
# containers (one download covers all 15 tasks). Only ``main`` carries
# ``build:``; bootstrap references the same image by tag (avoids BuildKit
# parallel-context race).
DOCKER_COMPOSE = """services:
  main:
    build:
      context: ..
      dockerfile: environment/Dockerfile
    image: ${COMPOSE_PROJECT_NAME}-img
    # /data/_cache is intentionally NOT mounted into main. /tests/ is not
    # mounted into main during agent runtime either (Harbor's convention --
    # the agent has no path to read test_labels.csv mid-run). Harbor
    # auto-mounts /tests/ when invoking the verifier (test.sh).
    volumes:
      - workspace-data:/workspace/data:rw
    depends_on:
      bootstrap:
        condition: service_completed_successfully
    environment:
      - PYTHONUNBUFFERED=1

  bootstrap:
    image: ${COMPOSE_PROJECT_NAME}-img
    # All host paths are relative to this compose file's location
    # (tasks/ehrshot/<task>/environment/) so the repo is portable across
    # users / machines. The Redivis token uses ${HOME} so it follows
    # whichever user is running Harbor.
    volumes:
      # Shared EHRSHOT bundle cache (RW so bootstrap can populate on cache
      # miss). Repo-relative: <repo_root>/scripts/ehrshot/assets/.
      - ../../../../scripts/ehrshot/assets:/data/_cache:rw
      # Redivis API token: needed if the cache is empty (downloads
      # ~4 GB from Redivis on first run). The file must exist at
      # $HOME/.redivis/api_token even on cache hit -- Docker resolves the
      # bind mount source at container creation time.
      - ${HOME}/.redivis/api_token:/root/.redivis/api_token:ro
      - workspace-data:/workspace/data:rw
      # Bootstrap writes test_labels.csv into tasks/<task>/tests/ at run
      # time. The file is gitignored so it never enters version control.
      # Harbor's verifier reads it from there when invoking test.sh.
      - ../tests:/tests:rw
    command: ["/bin/bash", "/bootstrap.sh"]

volumes:
  workspace-data:
"""


# Bootstrap script: per-container, idempotent, flock-serialized cold download.
# - Cache hit: exits in <1 s, no network.
# - Cache miss: pulls EHRSHOT_ASSETS.zip from Redivis (~4 GB compressed, ~17 GB
#   extracted), extracts under flock, chmod a-w on every file inside the lock
#   so a concurrent bootstrap on a different task can't race against partial
#   state. After unlock, stages this task's slice into the workspace-data
#   named volume that main shares.
BOOTSTRAP_SH = r"""#!/bin/bash
# One-shot bootstrap container for the ehrshot benchmark. Compose starts this
# service, waits for it to exit cleanly, and only then brings the main
# service up (via depends_on: condition: service_completed_successfully).
#
# Responsibilities:
#   1. If /data/_cache/EHRSHOT_ASSETS/ is missing the key bundle files,
#      download and extract EHRSHOT_ASSETS.zip from Redivis (gated on a
#      long-lived API token mounted at /root/.redivis/api_token).
#      Cache-hit is detected by file presence -- no marker file written.
#   2. Stage this task's data into /workspace/data/ via the shared
#      workspace-data named volume.
#
# When this script exits 0, Compose lets main start.
set -euo pipefail

TASK_ID="{task_id}"
CACHE=/data/_cache
ASSETS="$CACHE/EHRSHOT_ASSETS"
GLOBAL_LOCK="$CACHE/.bootstrap.lock"
TOKEN_FILE=/root/.redivis/api_token

mkdir -p "$CACHE" /workspace/data /workspace/submission

# Cache-hit check: presence of the key bundle files. Treat the cache as
# valid if these are all non-empty. This works whether the host pre-
# populated the bundle (via scripts/ehrshot/download.py) or a previous
# bootstrap run downloaded it -- no marker file needed.
_cache_ok() {{
    [ -s "$ASSETS/data/ehrshot.csv" ] \
        && [ -s "$ASSETS/splits/person_id_map.csv" ] \
        && [ -s "$ASSETS/features/count_features.pkl" ]
}}

_fetch() {{
    if _cache_ok; then
        echo "[bootstrap] cache hit: $ASSETS"
        return
    fi
    if [ ! -f "$TOKEN_FILE" ] || [ ! -s "$TOKEN_FILE" ]; then
        echo "[bootstrap] no Redivis API token at $TOKEN_FILE." 1>&2
        echo "  Accept the EHRSHOT data-use agreement at" 1>&2
        echo "  https://redivis.com/datasets/53gc-8rhx41kgt and write your" 1>&2
        echo "  token to ~/.redivis/api_token on the host." 1>&2
        exit 2
    fi
    echo "[bootstrap] cache miss; downloading EHRSHOT_ASSETS.zip from Redivis (~4 GB)..."
    REDIVIS_API_TOKEN="$(cat "$TOKEN_FILE")" python3 - <<'PYEOF'
import os, sys, zipfile, shutil
from pathlib import Path
import redivis
token = os.environ["REDIVIS_API_TOKEN"].strip()
if hasattr(redivis, "set_api_token"):
    try: redivis.set_api_token(token)
    except Exception: pass
cache = Path("/data/_cache")
zpath = cache / "EHRSHOT_ASSETS.zip"
table = redivis.table("shahlab.ehrshot:53gc:v3_0.files:4avd")
table.file("EHRSHOT_ASSETS.zip").download(str(cache), overwrite=True)
print(f"[bootstrap] extracting {{zpath}} -> {{cache}}", file=sys.stderr)
with zipfile.ZipFile(zpath) as z:
    z.extractall(cache)
zpath.unlink(missing_ok=True)
macosx = cache / "__MACOSX"
if macosx.is_dir():
    shutil.rmtree(macosx)
PYEOF
}}

# Serialize cold downloads across concurrent task containers. (Cache-hit
# branch is also serialized but exits in well under a second.)
exec 9>"$GLOBAL_LOCK"
flock 9
_fetch
flock -u 9

# Per-task data slicing. Writes the agent-visible artifacts to
# /workspace/data/ AND writes the verifier-only test_labels.csv into
# /tests/ (RW-mounted from host tasks/<task>/tests/; main does NOT see
# /tests/ during agent runtime per Harbor's default).
python3 /opt/ehrshot/stage_data.py --task-id "$TASK_ID" \
    --test-subset last \
    --private /tests

echo "[bootstrap] done -- main can start"
"""


VERIFY_PY = """#!/usr/bin/env python3
\"\"\"Per-task verifier entry point. Calls harbor_evaluator.evaluate.\"\"\"

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harbor_evaluator import evaluate  # noqa: E402


def main() -> None:
    here = Path(__file__).resolve().parent
    submission = Path("/workspace/submission/predictions.csv")
    test_labels = here / "test_labels.csv"   # written by bootstrap at run time
    baseline = here / "baseline.json"
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, test_labels, baseline, log_dir)
    print(f"auroc={score:.6f}")


if __name__ == "__main__":
    main()
"""


TEST_SH = """#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p /logs/verifier /logs/artifacts
python verify.py
"""


HARBOR_EVALUATOR_STUB = """\"\"\"Per-task trial-side verifier.

Runs inside the agent container under /tests/. The bootstrap service
derived test_labels.csv from the bundle at run time and wrote it to
/tests/test_labels.csv (RW-bind to host tasks/<task>/tests/ during
bootstrap; main does NOT have /tests/ mounted at agent runtime, so the
agent cannot read these labels during their work). The file is git-
ignored so it never enters version control. We compare the agent's
submission to those labels and write AUROC, AUPRC, and Brier to
/logs/verifier/reward.json.
\"\"\"

from __future__ import annotations

import json
import sys
from pathlib import Path

# /opt/ehrshot/evaluate.py is baked into the image by the Dockerfile.
sys.path.insert(0, \"/opt/ehrshot\")
import evaluate as _ev  # noqa: E402


def evaluate(
    submission_path: Path,
    test_labels_path: Path,
    baseline_path: Path,
    log_dir: Path,
) -> float:
    log_dir.mkdir(parents=True, exist_ok=True)
    baseline_meta = json.loads(baseline_path.read_text())
    task_id = baseline_meta[\"task_id\"]
    baseline_auroc = baseline_meta.get(\"baseline_auroc\")

    result = _ev.score_submission(
        submission_path=submission_path,
        test_labels_path=test_labels_path,
        task_id=task_id,
        baseline_auroc=baseline_auroc,
    )

    # Reward is BINARY (1.0 = passed baseline, 0.0 = did not). This matches
    # the convention used by other Harbor benchmarks (e.g. ct_abnormality)
    # so the launcher's \"Mean reward\" column reports the pass rate and
    # \"Successes\" reports the pass count. The actual continuous AUROC is
    # carried separately as `auroc` and can be requested via
    # --metric-to-report auroc.
    #
    # Harbor's VerifierResult pydantic schema requires every value in
    # reward.json to be float | int (no strings, no nested dicts).
    success_int = int(bool(result.passed)) if result.passed is not None else 0
    # NOTE: do not emit per-trial ``success`` — the launcher's ``_resolve_metric``
    # prefers per-trial values when present, which would render ``success`` as the
    # rate (mean of 0/1) instead of the count. ct_abnormality follows the same
    # pattern; the aggregator below derives count from ``reward``.
    reward_payload: dict[str, float | int] = {
        \"reward\": float(success_int),
        \"auroc\": float(result.auroc),
        \"auprc\": float(result.auprc),
        \"brier\": float(result.brier),
        \"n_test\": int(result.n_test),
        \"baseline_auroc\": float(baseline_auroc) if baseline_auroc is not None else -1.0,
    }
    metrics_payload = dict(reward_payload)
    metrics_payload[\"task_id\"] = task_id
    if result.per_subtask is not None:
        metrics_payload[\"per_subtask_auroc\"] = result.per_subtask
    (log_dir / \"reward.json\").write_text(json.dumps(reward_payload, indent=2))
    (log_dir / \"metrics.json\").write_text(json.dumps(metrics_payload, indent=2))
    return float(result.auroc)
"""


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------


def _ensure_clean(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Hardcoded fallback baselines.
#
# These mirror the values produced by ``scripts/ehrshot/reproduce_all_tasks.py``
# (count + LightGBM at k=-1, scored on the last-row-per-patient test subset)
# and ``scripts/ehrshot/reproduce_clmbr.py`` (clmbr + lr_lbfgs, same subset).
# Both reproduced the published EHRSHOT numbers to 3-4 decimal places.
#
# When the host-side ``scripts/ehrshot/assets/baselines.csv`` /
# ``baselines_clmbr.csv`` files are missing (e.g. a fresh clone, or because
# the user wiped ``scripts/ehrshot/assets/``), the generator falls back to
# these constants so the gate is always populated in ``baseline.json``.
# Re-running the reproducer scripts will regenerate the CSVs and the next
# ``generate_harbor_tasks.py`` invocation will prefer the CSV values (which
# may differ by ~0.001 across LightGBM threading runs).
# ---------------------------------------------------------------------------
_HARDCODED_BASELINE_AUROC_LAST: dict[str, float] = {
    "guo_icu":              0.8058511171225329,
    "guo_los":              0.8194828035866486,
    "guo_readmission":      0.7541908543859649,
    "new_acutemi":          0.7448820775146144,
    "new_celiac":           0.6027499070977332,
    "new_hyperlipidemia":   0.7001277139208173,
    "new_hypertension":     0.6868928457574257,
    "new_lupus":            0.7191385462297937,
    "new_pancan":           0.8707879959144543,
    "lab_anemia":           0.8205884925358547,
    "lab_hyperkalemia":     0.7527344019920002,
    "lab_hypoglycemia":     0.7142664869121013,
    "lab_hyponatremia":     0.7085620181757775,
    "lab_thrombocytopenia": 0.7855301204391551,
    "chexpert":             0.6819744631224808,
}

_HARDCODED_CLMBR_BASELINE_AUROC_LAST: dict[str, float] = {
    "guo_icu":              0.885261997795812,
    "guo_los":              0.8522923694043076,
    "guo_readmission":      0.8538603071604938,
    "new_acutemi":          0.7422126884451058,
    "new_celiac":           0.4855691812213552,
    "new_hyperlipidemia":   0.667352539800881,
    "new_hypertension":     0.7359696517412935,
    "new_lupus":            0.8009116593240833,
    "new_pancan":           0.8064033239003663,
    "lab_anemia":           0.9477135432170127,
    "lab_hyperkalemia":     0.7758894879725525,
    "lab_hypoglycemia":     0.8032872925533276,
    "lab_hyponatremia":     0.7630712275249438,
    "lab_thrombocytopenia": 0.8177523974635687,
    "chexpert":             0.7380103049619665,
}


def _read_baseline_auroc_last(
    baselines_csv: Path,
    task_id: str,
    fallback: dict[str, float] | None = None,
) -> float | None:
    """Read ``auroc_last`` from a host-side baselines CSV produced by
    ``reproduce_all_tasks.py`` (count+gbm) or ``reproduce_clmbr.py``
    (clmbr+lr_lbfgs). Falls back to a hardcoded constant dict (passed
    by the caller) when the CSV is missing or doesn't have a row for
    ``task_id``. Returns None only if both sources lack the task.
    """
    if baselines_csv.is_file():
        with baselines_csv.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("task") == task_id:
                    try:
                        return float(row["auroc_last"])
                    except (KeyError, ValueError, TypeError):
                        break
    if fallback is not None and task_id in fallback:
        return fallback[task_id]
    return None


def _count_test_rows(assets_dir: Path, task_id: str, test_subset: str = "last") -> int:
    """Compute how many test rows this task will have once the bootstrap
    container derives the test_labels.csv at run time. Stored in baseline.json
    for reference (we don't write the labels at generation time anymore — the
    bootstrap does that during ``stage_data.py``).
    """
    labels = stage_data.load_labels(assets_dir, task_id)
    labels = stage_data.attach_split(labels, assets_dir / "splits" / "person_id_map.csv")
    test = labels[labels["split"] == "test"].reset_index(drop=True)
    return len(stage_data.filter_test_subset(test, test_subset))


def _build_task(
    task_root: Path,
    entry: dict,
    assets_dir: Path,
    host_cache: Path,
    host_token: Path,
) -> None:
    _ensure_clean(task_root)
    task_id = entry["id"]
    kind = entry["kind"]
    description = entry.get("description", "").rstrip()
    label_semantics = entry.get("label_semantics", "").rstrip()
    submission_columns = entry.get("submission_columns", [])

    is_multilabel = kind == "multilabel"
    task_kind_title = "Multilabel prediction" if is_multilabel else "Binary prediction"
    if is_multilabel:
        # Chexpert: each of the 14 columns is an independent binary label
        # (1 = present, 0 = absent). Multiple labels can be 1 for the same
        # row -- this is multilabel, not multi-class. Probabilities across
        # the 14 columns are independent (do NOT softmax).
        multilabel_note = (
            ". The `label` field expands into 14 independent binary columns "
            "(one per finding); for each, `1` = present and `0` = absent. "
            "Multiple findings can be present in the same row"
        )
    else:
        multilabel_note = ""

    # Render the submission columns as a code block in instruction.md.
    submission_columns_block = (
        "\n\n    " + ",".join(submission_columns) + "\n"
        if submission_columns
        else "\n\n    patient_id,prediction_time,probability\n"
    )

    _write(
        task_root / "task.toml",
        TASK_TOML.format(task_id=task_id),
    )
    _write(
        task_root / "instruction.md",
        INSTRUCTION_MD.format(
            task_id=task_id,
            task_kind_title=task_kind_title,
            task_description=description or "(see task documentation)",
            label_semantics=label_semantics or "(see task documentation)",
            multilabel_note=multilabel_note,
            submission_columns_block=submission_columns_block,
        ),
    )

    env_dir = task_root / "environment"
    tests_dir = task_root / "tests"
    env_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    # No environment/workspace/ directory: workspace/data/ is populated at
    # runtime by the bootstrap service via the workspace-data named volume.

    _write(env_dir / "Dockerfile", DOCKERFILE)
    # Compose template uses portable repo-relative + ${HOME} paths; no
    # format substitution needed (template still has Compose-level
    # ${VAR} sequences that escape as {{ }} in the Python source).
    _write(env_dir / "docker-compose.yaml", DOCKER_COMPOSE)
    bootstrap_path = env_dir / "bootstrap.sh"
    _write(bootstrap_path, BOOTSTRAP_SH.format(task_id=task_id))
    bootstrap_path.chmod(0o755)

    # Bake stage_data.py + evaluate.py into the per-task environment so the
    # Dockerfile's COPY directives find them at build time.
    here = Path(__file__).resolve().parent
    shutil.copy2(here / "stage_data.py", env_dir / "stage_data.py")
    shutil.copy2(here / "evaluate.py", env_dir / "evaluate.py")

    # Test labels are NOT pre-committed at generation time. The bootstrap
    # container derives them from the bundle at run time and writes them
    # to /tests/test_labels.csv (verifier-only, agent should not access
    # /tests/). We just record the expected row count here for reference.
    n_test = _count_test_rows(assets_dir, task_id, test_subset="last")
    # Defensive cleanup: stale test_labels.csv from older designs would
    # bypass the new "downloaded at run time" rule.
    stale = tests_dir / "test_labels.csv"
    if stale.exists():
        stale.unlink()

    # baseline.json: pass-gate AUROC on the LAST-per-patient subset.
    # We record both count+gbm (the active gate) and clmbr+lr_lbfgs
    # (informational; the EHRSHOT foundation-model baseline) so we can
    # switch the gate later without regenerating. Both numbers fall back
    # to hardcoded constants (mirroring the reproduced EHRSHOT baselines)
    # when the CSVs aren't on disk, so a fresh clone without
    # ``scripts/ehrshot/assets/baselines{,_clmbr}.csv`` still produces
    # valid baseline.json gates.
    assets_root = REPO_ROOT / "scripts" / "ehrshot" / "assets"
    gbm_auroc = _read_baseline_auroc_last(
        assets_root / "baselines.csv", task_id,
        fallback=_HARDCODED_BASELINE_AUROC_LAST,
    )
    clmbr_auroc = _read_baseline_auroc_last(
        assets_root / "baselines_clmbr.csv", task_id,
        fallback=_HARDCODED_CLMBR_BASELINE_AUROC_LAST,
    )
    baseline_payload = {
        "task_id": task_id,
        "kind": kind,
        "test_subset": "last",
        "n_test": n_test,
        # Active gate: count + LightGBM (the simple-features EHRSHOT baseline).
        "baseline_model": "count + LightGBM",
        "baseline_auroc": gbm_auroc,
        "baseline_source": (
            "scripts/ehrshot/assets/baselines.csv :: auroc_last "
            "(count+gbm refit on EHRSHOT train+val, scored on last-row-per-patient test subset)"
        ),
        # Informational secondary baseline: CLMBR + L2 logistic regression
        # (LBFGS solver, MaxAbsScaler), the EHRSHOT-published foundation-
        # model baseline. NOT the current pass gate -- record for reference;
        # we may switch the gate to this later without re-running anything.
        "clmbr_baseline_model": "clmbr + lr_lbfgs",
        "clmbr_baseline_auroc": clmbr_auroc,
        "clmbr_baseline_source": (
            "scripts/ehrshot/assets/baselines_clmbr.csv :: auroc_last "
            "(clmbr+lr_lbfgs refit on EHRSHOT train+val, scored on last subset)"
        ),
    }
    _write(tests_dir / "baseline.json", json.dumps(baseline_payload, indent=2))

    _write(tests_dir / "harbor_evaluator.py", HARBOR_EVALUATOR_STUB)
    _write(tests_dir / "verify.py", VERIFY_PY)
    test_sh = tests_dir / "test.sh"
    _write(test_sh, TEST_SH)
    test_sh.chmod(0o755)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=None,
        help=(
            "Host path to bind-mount RO into each task container at "
            "/data/_cache (default: scripts/ehrshot/assets/EHRSHOT_ASSETS's "
            "parent, or $EHRSHOT_ASSETS_DIR's parent). The bootstrap service "
            "downloads into this directory on cache miss; subsequent task "
            "containers reuse it."
        ),
    )
    parser.add_argument(
        "--token-file",
        type=Path,
        default=Path.home() / ".redivis" / "api_token",
        help="Host path to the Redivis API token file (default: %(default)s).",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Don't run the host-side download check. Use only an existing cache.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=TASK_CONFIGS,
        help="Path to task_configs.yaml (default: %(default)s).",
    )
    parser.add_argument(
        "--tasks-root",
        type=Path,
        default=TASKS_ROOT,
        help="Where to write generated task folders (default: %(default)s).",
    )
    args = parser.parse_args(argv)

    # Resolve the host cache directory. The bootstrap container mounts this
    # path at /data/_cache and downloads EHRSHOT_ASSETS/ into it. We use the
    # parent of the assets root so the bundle ends up at
    # <host_cache>/EHRSHOT_ASSETS/, matching what download.py would produce.
    if args.assets_dir is not None:
        assets_dir = args.assets_dir.resolve()
    else:
        assets_dir = default_assets_dir().resolve()
    host_cache = assets_dir.parent
    host_cache.mkdir(parents=True, exist_ok=True)
    host_token = args.token_file.resolve()

    # Bundle must be present on host at generation time so we can write
    # tests/test_labels.csv and resolve baseline_auroc per task. Bootstrap
    # also downloads-on-demand inside the container, but the host needs it
    # too. download.main() is idempotent on a populated cache.
    if not args.skip_download:
        rc = download_main(["--assets-dir", str(assets_dir)])
        if rc != 0:
            return rc

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    tasks = manifest.get("tasks", [])
    if not tasks:
        print(
            f"[ehrshot-generate] manifest at {args.manifest} has no enabled tasks.",
            file=sys.stderr,
        )
        return 1

    args.tasks_root.mkdir(parents=True, exist_ok=True)
    readme = args.tasks_root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# ehrshot Harbor tasks\n\n"
            "Generated by `scripts/ehrshot/generate_harbor_tasks.py`. Do not edit by hand.\n"
        )

    for entry in tasks:
        task_id = entry["id"]
        task_root = args.tasks_root / task_id
        kind = entry.get("kind", "binary")
        print(f"[ehrshot-generate] {task_id} ({kind})", file=sys.stderr)
        _build_task(task_root, entry, assets_dir, host_cache, host_token)

    print(
        f"[ehrshot-generate] OK: wrote {len(tasks)} task folders under {args.tasks_root}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
