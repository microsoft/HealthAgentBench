"""Generate Harbor task subdirectories for the ehr_data_quality benchmark.

For each task entry in ``assets/task_configs.yaml`` this writes:

    tasks/ehr_data_quality/<task_id>/
        task.toml
        instruction.md
        environment/
            Dockerfile
            workspace/
                README.md
                stage_data.py
                inject.py
                task_config.yaml
        tests/
            test.sh
            verify.py
            harbor_evaluator.py
            labels.csv            # only if --regenerate-labels is set,
                                      # otherwise expected to be checked in.

Usage:

    uv run python scripts/ehr_data_quality/generate_harbor_tasks.py \\
        --output-root tasks/ehr_data_quality

The Docker build context is rooted at ``<task_dir>/environment``. So any
file the Dockerfile needs at build time (the labels.csv for the build-time
verification step) is staged into ``environment/build_inputs/`` by this
generator.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from hashlib import sha1
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPTS_DIR / "assets"
TASK_CONFIGS_PATH = ASSETS / "task_configs.yaml"
PYTHON_BASE = "3.12-slim"
PIP_PINS = "pandas==3.0.1 pyarrow==23.0.1 duckdb==1.5.2 numpy==2.4.2 pyyaml==6.0.3"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _ensure_clean(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Per-task content
# ---------------------------------------------------------------------------


def build_task_toml(task_id: str) -> str:
    return f"""version = "1.0"

[metadata]
benchmark = "ehr_data_quality"
mode = "etl-task"
task_id = "{task_id}"
submission_path = "/workspace/submission/flagged_rows.csv"

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 3600.0

[environment]
build_timeout_sec = 1800.0
allow_internet = true
cpus = 2
memory_mb = 4096
storage_mb = 10240
gpus = 0
mcp_servers = []

[verifier.env]

[solution.env]
"""


CATEGORY_DESCRIPTIONS = {
    "impossible_value": (
        "**Impossible values** — a recorded entry whose numeric content or "
        "unit label is implausible for what it represents."
    ),
    "temporal_violation": (
        "**Temporal inconsistencies** — timestamps that are logically out of "
        "order across columns or across tables."
    ),
    "inconsistency": (
        "**Conflicting records** — two records that should describe the same "
        "observation for the same patient at the same time but disagree."
    ),
    "demographic_conflict": (
        "**Demographic contradictions** — the patient's recorded demographic "
        "information contradicts other evidence about that patient."
    ),
}


# Per-subtype descriptions used by the subtype_view tasks. The agent's
# instruction lists only the specific subtype the view is scoring on.
SUBTYPE_DESCRIPTIONS = {
    # impossible_value subtypes
    "range_extreme": (
        "**Physiologically impossible values** — a numeric measurement whose "
        "value lies outside the plausible physiological range for the "
        "measurement type."
    ),
    "decimal_shift": (
        "**Decimal-shift errors in lab / chart measurements**"
    ),
    "decimal_shift_rx": (
        "**Decimal-shift errors in prescription doses**"
    ),
    "unit_confusion": (
        "**Unit-conversion mistakes**"
    ),
    "valueuom_mismatch": (
        "**Unit-label mismatches**"
    ),
    # inconsistency subtypes
    "in_table_conflict": (
        "**Within-table conflicts** — two rows in the same table that "
        "should agree on a measurement but record disagreeing values."
    ),
    "cross_table_conflict": (
        "**Cross-table conflicts** — two rows in different tables that record the same conceptual "
        "measurement for the same patient at the same time, but with "
        "disagreeing values."
    ),
    # demographic_conflict subtypes
    "gender_via_patients_flip": (
        "**Patient-gender mismatches** — the patient's recorded gender contradicts other in-record evidence"
    ),
    # gender_via_prescription_swap removed as a standalone view task.
    # gender_via_ref_range_swap removed from the suite — see comment in
    # inject.py's apply_task_corruption post-hoc filter for rationale.
    "age_via_patients_change": (
        "**Age contradictions** — a row in `patients` whose recorded age "
        "contradicts other evidence about that patient"
    ),
}


def build_instruction(families: list[str]) -> str:
    """Build a per-task instruction.md. The prompt frames the task generically
    ("flag data entry errors") and lists the per-task error categories so the
    agent knows the scope of detection it's being graded on."""
    bullets = "\n".join(
        f"{i + 1}. {CATEGORY_DESCRIPTIONS[fam]}" for i, fam in enumerate(families)
    )
    category_noun = "category" if len(families) == 1 else "categories"

    return f"""# EHR Data-Quality Detection

You are working inside a task environment that contains a copy of an EHR
dataset under `/workspace/data/`. Do a data quality check of the EHR
dataset and flag data entry errors belonging to certain error categories.
Submit the rows you identify at
`/workspace/submission/flagged_rows.csv`.

**You have up to 1 hour to complete this task.**

## Categories of errors to look for
You should flag all errors belonging to the following {category_noun}:

{bullets}

Be thorough and make sure to flag all such errors.

## Submission format

A CSV with these columns:

- `table`: one of patients, admissions, labevents, prescriptions,
  d_labitems, icustays, chartevents, d_items
- `_row_id`: the value of the `_row_id` column for the row you are flagging

## Data

EHR tables are at `/workspace/data/csv/<table>.csv.gz` (gzipped CSVs).

## Rules

You should not cheat and you should not directly look up for the end
solutions from the internet.
"""


WORKSPACE_README = """# Workspace orientation

This workspace contains a corrupted EHR dataset under `data/`. See
`../instruction.md` for the task description.

Layout:

- `data/csv/<table>.csv.gz`: eight EHR tables (gzipped CSVs).
- `submission/flagged_rows.csv`: write your answer here.

The schema across tables follows a typical hospital + ICU layout: patients,
admissions, lab events, prescriptions, ICU stays, chart events, plus two
dictionary tables (`d_labitems`, `d_items`).
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
    submission = Path("/workspace/submission/flagged_rows.csv")
    # /tests/ is mounted by Harbor only at verifier-runtime; the agent phase
    # never sees this path. test.sh cd's here before invoking verify.py so
    # labels.csv resolves to the source-tree's tasks/<task>/tests/labels.csv.
    labels = Path(__file__).resolve().parent / "labels.csv"
    log_dir = Path("/logs/verifier")
    f1 = evaluate(submission, labels, log_dir)
    print(f"f1={f1:.6f}")


if __name__ == "__main__":
    main()
"""


def build_dockerfile() -> str:
    """Generated Dockerfile (shared between ``bootstrap`` and ``main``).

    The image is intentionally task-content-free: no ``inject.py``,
    ``stage_data.py``, ``task_config.yaml``, or ``labels.csv`` is baked in.
    The bootstrap compose service bind-mounts those at ``/opt/bootstrap_inputs``
    and runs the corruption pipeline into a named volume; the main service
    (where the agent runs) only mounts that volume read-only, so it never
    sees the staging scripts or the gold labels. This follows the same
    two-service pattern used by ``xray_report_gen``.
    """
    return f"""FROM python:{PYTHON_BASE}

# bash + flock for the bootstrap script; curl/wget for the MIMIC-IV demo
# download that stage_data.py performs on cache miss.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
       bash ca-certificates curl wget util-linux \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir {PIP_PINS}

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# Compose's build context is the parent (task root), so the path is
# environment/workspace/ rather than workspace/. Match xray_report_gen.
COPY environment/workspace/ /workspace/
RUN mkdir -p /workspace/data /workspace/submission /logs/verifier

# No ENTRYPOINT / CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive for the agent
# + verifier. The bootstrap service uses an explicit ``command:`` in
# docker-compose.yaml to run /bootstrap.sh (bind-mounted) and exit.
"""


def build_docker_compose() -> str:
    """Two-service compose: bootstrap stages corrupted data, main runs the agent."""
    return """services:
  bootstrap:
    image: ${COMPOSE_PROJECT_NAME}-main
    build:
      context: ..
      dockerfile: environment/Dockerfile
    volumes:
      # Staging scripts (inject.py, stage_data.py, task_config.yaml)
      # bind-mounted into bootstrap only. The main service (where the
      # agent runs) never sees this path.
      - ./bootstrap_inputs:/opt/bootstrap_inputs:ro
      - ./bootstrap.sh:/bootstrap.sh:ro
      # Gold labels — single source of truth at tests/labels.csv. Mounted
      # read-only into bootstrap so the --verify-against check has the
      # same file the verifier uses. NOT mounted into main; Harbor mounts
      # /tests/ into a separate verifier exec at scoring time.
      - ../tests:/tests:ro
      # Host-side cache of the MIMIC-IV-demo raw CSVs, shared across trials
      # so the ~30s download happens at most once per machine.
      - ../../../../scripts/ehr_data_quality/assets/raw_cache:/data/_src/raw_cache:rw
      # Named volume that carries the corrupted /workspace/data into main.
      - task-data:/workspace/data:rw
    environment:
      - PYTHONUNBUFFERED=1
    command: ["/bin/bash", "/bootstrap.sh"]

  main:
    image: ${COMPOSE_PROJECT_NAME}-main
    build:
      context: ..
      dockerfile: environment/Dockerfile
    depends_on:
      bootstrap:
        condition: service_completed_successfully
    volumes:
      # Agent sees ONLY the corrupted data, read-only. No inject.py /
      # stage_data.py / task_config.yaml / labels.csv on this filesystem.
      - task-data:/workspace/data:ro
    environment:
      - PYTHONUNBUFFERED=1
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

volumes:
  task-data:
"""


def build_bootstrap_sh() -> str:
    """Bind-mounted entry script for the bootstrap compose service."""
    return """#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Stage the corrupted MIMIC-IV-demo subset for this task.
#
# Inputs (bind-mounted into bootstrap, NEVER into main):
#   /opt/bootstrap_inputs/inject.py
#   /opt/bootstrap_inputs/stage_data.py
#   /opt/bootstrap_inputs/task_config.yaml
#   /tests/labels.csv                     (gold, read-only — single source
#                                          of truth shared with the verifier)
#
# Output (named volume shared with main):
#   /workspace/data/csv/<table>.csv.gz    (eight EHR tables, partially corrupted)
#
# Cross-trial cache (host bind-mount):
#   /data/_src/raw_cache                  (MIMIC-IV-demo raw CSVs)
# ---------------------------------------------------------------------------

LOCK_DIR=/data/_src/raw_cache/.bootstrap.locks
mkdir -p "$LOCK_DIR"

# Global lock: concurrent trials share the raw_cache download. First trial to
# acquire the lock fills the cache; others wait, then read from it.
exec 9>"$LOCK_DIR/global.lock"
flock 9

# Run the corruption pipeline. --input-dir reuses the bind-mounted raw_cache
# so the MIMIC-IV-demo download happens at most once per host. --verify-against
# asserts the freshly-corrupted data matches the gold labels.csv bit-for-bit;
# if inject.py drifts from labels.csv this fails loudly and Harbor aborts the
# trial before the agent ever starts (preventing silently-broken runs).
python /opt/bootstrap_inputs/stage_data.py \\
    --config /opt/bootstrap_inputs/task_config.yaml \\
    --output-dir /workspace/data \\
    --input-dir /data/_src/raw_cache \\
    --verify-against /tests/labels.csv \\
    --no-duckdb

echo "[bootstrap] corrupted data staged at /workspace/data, verify-against passed."
"""


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _slice_task(all_configs: list[dict], task_id: str) -> dict[str, Any]:
    for entry in all_configs:
        if entry["id"] == task_id:
            return entry
    raise KeyError(f"task {task_id} not found in task_configs.yaml")


def _compute_cache_key(task_config: dict) -> str:
    """Hash inputs that affect label generation. Sidecar `.sha1` files at
    ``assets/labels/<task_id>.csv.sha1`` store this key alongside cached
    labels so we can auto-invalidate when any input changes."""
    inject_src = (SCRIPTS_DIR / "inject.py").read_bytes()
    stage_src = (SCRIPTS_DIR / "stage_data.py").read_bytes()
    config_bytes = yaml.safe_dump(task_config, sort_keys=False).encode("utf-8")
    h = sha1()
    h.update(b"inject.py:");   h.update(inject_src)
    h.update(b"\nstage_data.py:"); h.update(stage_src)
    h.update(b"\ntask_config:"); h.update(config_bytes)
    return h.hexdigest()


def _build_task(
    task_root: Path,
    task_config: dict,
    *,
    use_cached_labels: bool,
) -> None:
    _ensure_clean(task_root)
    task_id = task_config["id"]

    _write(task_root / "task.toml", build_task_toml(task_id))
    # instruction.md is tailored per task: it names only the error families
    # actually present in this task. Order in the YAML defines the order of
    # categories shown to the agent.
    families = [spec["family"] for spec in task_config.get("injectors", [])]
    if not families:
        raise ValueError(f"task {task_id} has no injectors configured")
    _write(task_root / "instruction.md", build_instruction(families))

    env_dir = task_root / "environment"
    workspace = env_dir / "workspace"
    bootstrap_inputs = env_dir / "bootstrap_inputs"
    tests_dir = task_root / "tests"

    # Clean up any legacy build_inputs/ directory from the pre-compose layout.
    legacy_build_inputs = env_dir / "build_inputs"
    if legacy_build_inputs.exists():
        shutil.rmtree(legacy_build_inputs)

    workspace.mkdir(parents=True, exist_ok=True)
    bootstrap_inputs.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Workspace is intentionally minimal: only a README explaining the
    # agent's environment. inject.py / stage_data.py / task_config.yaml all
    # live under bootstrap_inputs/ now (bind-mounted into the bootstrap
    # compose service only — the agent's main service never sees them).
    _write(workspace / "README.md", WORKSPACE_README)

    # bootstrap_inputs/: everything the bootstrap container needs to stage
    # the corrupted data. Not COPYed into the image — bind-mounted into the
    # bootstrap service only via docker-compose.yaml.
    shutil.copyfile(SCRIPTS_DIR / "stage_data.py", bootstrap_inputs / "stage_data.py")
    shutil.copyfile(SCRIPTS_DIR / "inject.py", bootstrap_inputs / "inject.py")
    _write(
        bootstrap_inputs / "task_config.yaml",
        yaml.safe_dump(task_config, sort_keys=False),
    )

    # Tests dir: agent-hidden labels go here; verifier glue comes from the
    # canonical scripts/ehr_data_quality harbor_evaluator copy.
    shutil.copyfile(
        SCRIPTS_DIR / "harbor_evaluator.py", tests_dir / "harbor_evaluator.py"
    )
    _write(tests_dir / "verify.py", VERIFY_PY)
    test_sh_path = tests_dir / "test.sh"
    _write(test_sh_path, TEST_SH)
    test_sh_path.chmod(0o755)

    # Labels: regenerate by default. ``--use-cached-labels`` enables the fast
    # path, but we still auto-invalidate the cache if inject.py /
    # stage_data.py / this task's config have changed since the cache was
    # written (per its sidecar ``.sha1`` file). This prevents the most common
    # foot-gun: stale labels lingering after a tweak to inject.py, which
    # would silently break the Dockerfile's ``--verify-against`` check.
    labels_src = ASSETS / "labels" / f"{task_id}.csv"
    sha1_src = labels_src.with_suffix(".csv.sha1")
    current_key = _compute_cache_key(task_config)
    cache_fresh = (
        labels_src.exists()
        and sha1_src.exists()
        and sha1_src.read_text().strip() == current_key
    )

    if use_cached_labels and cache_fresh:
        pass  # fast path — cache is valid
    else:
        if use_cached_labels and labels_src.exists() and not cache_fresh:
            print(
                f"  [{task_id}] cache stale (inject.py / stage_data.py / "
                f"task_config changed); regenerating",
                flush=True,
            )
        _generate_labels(task_config, labels_src)
        sha1_src.write_text(current_key + "\n")

    shutil.copyfile(labels_src, tests_dir / "labels.csv")
    # No duplicate copy in bootstrap_inputs/ — bootstrap.sh reads the
    # canonical tests/labels.csv via a read-only bind-mount of ../tests
    # declared in docker-compose.yaml. Main never mounts tests/, so the
    # agent still can't see labels.csv at runtime.

    # Dockerfile + docker-compose.yaml + bootstrap.sh.
    _write(env_dir / "Dockerfile", build_dockerfile())
    _write(env_dir / "docker-compose.yaml", build_docker_compose())
    bootstrap_sh_path = env_dir / "bootstrap.sh"
    _write(bootstrap_sh_path, build_bootstrap_sh())
    bootstrap_sh_path.chmod(0o755)


def build_view_instruction(subtype: str) -> str:
    """Instruction.md for a subtype-view task. Names exactly one category."""
    if subtype not in SUBTYPE_DESCRIPTIONS:
        raise KeyError(
            f"no SUBTYPE_DESCRIPTIONS entry for subtype {subtype!r}; "
            "add one in generate_harbor_tasks.py"
        )
    bullet = f"1. {SUBTYPE_DESCRIPTIONS[subtype]}"

    return f"""# EHR Data-Quality Detection

You are working inside a task environment that contains a copy of an EHR
dataset under `/workspace/data/`. Do a data quality check of the EHR
dataset and flag data entry errors belonging to certain error categories.
Submit the rows you identify at
`/workspace/submission/flagged_rows.csv`.

**You have up to 1 hour to complete this task.**

## Categories of errors to look for
You should flag all errors belonging to the following category:

{bullet}

Be thorough and make sure to flag all such errors.

## Submission format

A CSV with these columns:

- `table`: one of patients, admissions, labevents, prescriptions,
  d_labitems, icustays, chartevents, d_items
- `_row_id`: the value of the `_row_id` column for the row you are flagging

## Data

EHR tables are at `/workspace/data/csv/<table>.csv.gz` (gzipped CSVs).

## Rules

You should not cheat and you should not directly look up for the end
solutions from the internet.
"""


def _filter_labels_by_subtype(parent_labels: Path, subtype: str) -> str:
    """Read parent task's labels.csv and return CSV text containing only
    rows belonging to clusters anchored by the named ``subtype``.

    A cluster is "anchored" by a subtype if at least one of its rows has
    ``error_subtype == subtype``. All rows sharing that cluster_id are
    kept (including evidence/anchor rows like
    ``gender_via_patients_flip_lab_evidence``) so the agent retains the
    same cluster-credit semantics it would have in the parent task.
    """
    import csv as _csv
    import io as _io

    with parent_labels.open("r", newline="") as f:
        reader = _csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)

    anchor_clusters = {
        r["cluster_id"] for r in rows if r.get("error_subtype") == subtype
    }
    kept = [r for r in rows if r.get("cluster_id") in anchor_clusters]

    buf = _io.StringIO()
    writer = _csv.DictWriter(buf, fieldnames=header)
    writer.writeheader()
    writer.writerows(kept)
    return buf.getvalue()


def _build_view_task(task_root: Path, view_cfg: dict, parent_cfg: dict) -> None:
    """Build a subtype-view task by reusing the parent's bootstrap pipeline
    and writing a filtered labels.csv + subtype-specific instruction.md.

    The agent sees the *same* corrupted CSVs as the parent task (the
    bootstrap regenerates them from the parent's task_config), but the
    verifier scores only on catching clusters anchored by
    ``view_cfg['subtype']``. Rows from other subtypes act as benign noise.
    """
    parent_id = parent_cfg["id"]
    subtype = view_cfg["subtype"]

    # Reuse _build_task's plumbing — pass the PARENT's config so all of
    # bootstrap_inputs/{inject.py, stage_data.py, task_config.yaml},
    # Dockerfile, docker-compose.yaml, and bootstrap.sh are identical to
    # the parent's. ``use_cached_labels`` is True so we don't re-run the
    # corruption pipeline; we just need the parent's labels.csv to land
    # in the view's tests/labels.csv. We then overwrite that file with
    # the filtered subset and overwrite instruction.md with the
    # subtype-specific text.
    _build_task(task_root, parent_cfg, use_cached_labels=True)

    # Overwrite instruction.md with the subtype-specific version.
    _write(task_root / "instruction.md", build_view_instruction(subtype))

    # Filter labels.csv down to clusters anchored by ``subtype``.
    parent_labels_cache = ASSETS / "labels" / f"{parent_id}.csv"
    if not parent_labels_cache.exists():
        raise FileNotFoundError(
            f"parent labels {parent_labels_cache} missing — make sure "
            f"task {parent_id} was generated before this view"
        )
    filtered_csv = _filter_labels_by_subtype(parent_labels_cache, subtype)
    n_lines = filtered_csv.count("\n") - 1  # minus header
    if n_lines <= 0:
        raise ValueError(
            f"subtype view {view_cfg['id']!r} produced 0 labeled clusters "
            f"after filtering {parent_id} by subtype {subtype!r}; check "
            f"that the parent task actually injects this subtype"
        )
    (task_root / "tests" / "labels.csv").write_text(filtered_csv)


def _generate_labels(task_config: dict, output_path: Path) -> None:
    """Run the corruption pipeline locally to compute labels for this task."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    from stage_data import main as stage_main  # noqa: E402

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cache_root = ASSETS / "raw_cache"
    config_dir = ASSETS / "_task_slices"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"{task_config['id']}.yaml"
    config_path.write_text(yaml.safe_dump(task_config, sort_keys=False))

    out_dir = config_dir / task_config["id"] / "data"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    args = [
        "--config",
        str(config_path),
        "--output-dir",
        str(out_dir),
        "--labels-output",
        str(output_path),
        "--no-duckdb",
    ]
    if cache_root.exists():
        args.extend(["--input-dir", str(cache_root)])
    stage_main(args)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "tasks" / "ehr_data_quality",
    )
    parser.add_argument(
        "--task-ids",
        type=str,
        default=None,
        help="Comma-separated subset (e.g. task_001,task_005). Default: all.",
    )
    parser.add_argument(
        "--use-cached-labels",
        action="store_true",
        help=(
            "Fast path: reuse the cached labels at "
            "scripts/ehr_data_quality/assets/labels/<task_id>.csv when its "
            "sidecar .sha1 still matches the hash of inject.py + "
            "stage_data.py + the task's config. Otherwise the cache is "
            "auto-invalidated and regenerated. Default (without this flag) "
            "is to always regenerate."
        ),
    )
    args = parser.parse_args(argv)

    raw_yaml = yaml.safe_load(TASK_CONFIGS_PATH.read_text())
    all_configs = raw_yaml["tasks"]
    all_views = raw_yaml.get("subtype_views", []) or []
    parent_by_id = {c["id"]: c for c in all_configs}

    if args.task_ids:
        wanted = {tid.strip() for tid in args.task_ids.split(",") if tid.strip()}
        all_configs = [c for c in all_configs if c["id"] in wanted]
        all_views = [v for v in all_views if v["id"] in wanted]
        # Ensure parents of any selected view get built too (views read the
        # parent's cached labels.csv).
        view_parents = {v["parent"] for v in all_views}
        for pid in view_parents:
            if pid not in {c["id"] for c in all_configs} and pid in parent_by_id:
                all_configs.append(parent_by_id[pid])

    args.output_root.mkdir(parents=True, exist_ok=True)
    _write(
        args.output_root / "README.md",
        "Generated by `scripts/ehr_data_quality/generate_harbor_tasks.py`.\n"
        "Each `task_NNN/` subdirectory is a complete Harbor task. "
        "See `scripts/ehr_data_quality/README.md` for benchmark details.\n",
    )

    # Phase 1: build parent tasks first so their labels are cached before
    # subtype_view tasks try to filter them.
    for cfg in all_configs:
        task_root = args.output_root / cfg["id"]
        print(f"Generating {task_root}", flush=True)
        _build_task(task_root, cfg, use_cached_labels=args.use_cached_labels)

    # Phase 2: build subtype-view tasks. Each view inherits everything from
    # its parent and only overrides labels.csv (filtered) + instruction.md
    # (subtype-specific).
    for view in all_views:
        parent_cfg = parent_by_id.get(view["parent"])
        if parent_cfg is None:
            raise KeyError(
                f"subtype_view {view['id']} references unknown parent "
                f"{view['parent']!r}; check task_configs.yaml"
            )
        task_root = args.output_root / view["id"]
        print(f"Generating {task_root} (view of {view['parent']}/{view['subtype']})", flush=True)
        _build_view_task(task_root, view, parent_cfg)


if __name__ == "__main__":
    main()
