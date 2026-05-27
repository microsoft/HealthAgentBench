"""Generate Harbor task subdirectories for the mimic_iv_dq benchmark.

For each task entry in ``assets/task_configs.yaml`` this writes:

    tasks/mimic_iv_dq/<task_id>/
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

    uv run python scripts/mimic_iv_dq/generate_harbor_tasks.py \\
        --output-root tasks/mimic_iv_dq

The Docker build context is rooted at ``<task_dir>/environment``. So any
file the Dockerfile needs at build time (the labels.csv for the build-time
verification step) is staged into ``environment/build_inputs/`` by this
generator.
"""

from __future__ import annotations

import argparse
import shutil
import sys
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
benchmark = "mimic_iv_dq"
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
        "**Impossible values** — a single field value that is implausible for "
        "the measurement type (e.g., physiologically impossible, or "
        "implausible for the displayed unit, or off by an obvious order of "
        "magnitude)."
    ),
    "temporal_violation": (
        "**Temporal inconsistencies** — timestamps that are logically out of "
        "order across columns or across tables (e.g., one event occurring "
        "before another that must necessarily precede it)."
    ),
    "inconsistency": (
        "**Conflicting / duplicate records** — two rows that should agree on "
        "a measurement but do not, either within one table or across tables "
        "that record the same conceptual measurement."
    ),
    "demographic_conflict": (
        "**Demographic contradictions** — a row in `patients` whose recorded "
        "gender or age contradicts other evidence about that patient (for "
        "example, the medications they were prescribed)."
    ),
}


def build_instruction(families: list[str]) -> str:
    """Build a per-task instruction.md whose error-category section lists only
    the families actually present in this task."""
    if len(families) == 1:
        intro = (
            "The injected issues fall into one category. Focus your detection "
            "on it — do not flag rows that are merely unusual but plausible."
        )
        scope = "Stay within this category."
    else:
        intro = (
            f"The injected issues fall into {len(families)} categories. "
            "Focus your detection on these — do not flag rows that are merely "
            "unusual but plausible."
        )
        scope = "Stay within these categories."

    bullets = "\n".join(
        f"{i + 1}. {CATEGORY_DESCRIPTIONS[fam]}" for i, fam in enumerate(families)
    )

    return f"""# EHR Data-Quality Detection

You are working inside a task environment that contains a copy of an EHR
dataset under `/workspace/data/`. A subset of rows has been deliberately
mutated to introduce data-quality issues. Your job is to identify which
rows are problematic and submit them at
`/workspace/submission/flagged_rows.csv`.

Be selective: both missing real issues and flagging legitimate rows will
affect your score. Submit only rows you have strong evidence are
problematic.

## Categories of errors to look for

{intro}

{bullets}

{scope} Generic "looks weird" outliers, clinically extreme but plausible
values, or rare-but-legitimate variation are not what we are looking for.

## Submission format

A CSV with these columns:

- `table`: one of patients, admissions, labevents, prescriptions,
  d_labitems, icustays, chartevents, d_items
- `_row_id`: the value of the `_row_id` column for the row you are flagging

## What you have

- `/workspace/data/csv/<table>.csv.gz`: the EHR tables (gzipped CSVs)
- Standard tools available: pandas, duckdb, numpy, pyarrow, sqlite3 — load
  the CSVs into whichever you prefer for querying.

## Rules

Do **not** use the internet to look up reference ranges, canonical units,
or the source dataset. Do **not** attempt to re-download a "pristine" copy
of the data and diff it against `/workspace/data/`. Solve the task using
only the data in `/workspace/data/` and standard analytical tools
(pandas, duckdb, numpy). Internet is enabled only to allow your runtime
to function; using it to retrieve answers is considered cheating.
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
    """Generated Dockerfile.

    Build context is the task's ``environment/`` directory. The
    ``build_inputs/labels.csv`` here is consumed transiently for build-time
    verification only — it is removed from the image in the same ``RUN``
    layer that uses it. The HOST-side ``tasks/<task>/tests/labels.csv`` is
    what the verifier reads at run time, mounted by Harbor only when the
    verifier executes (the agent phase never sees ``/tests/``). This
    follows the same pattern used by ``xray_report_gen``.
    """
    return f"""FROM python:{PYTHON_BASE}

RUN apt-get update \\
    && apt-get install -y --no-install-recommends bash ca-certificates curl git \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir {PIP_PINS}

WORKDIR /workspace
COPY workspace/ /workspace/

# Stage data: download demo, apply corruption, verify against the build-time
# labels copy, then erase BOTH the staging scripts AND the build-time labels
# copy in the same layer so the agent never sees them in the merged view.
COPY build_inputs/labels.csv /tmp/build_labels.csv
RUN python /workspace/stage_data.py \\
        --config /workspace/task_config.yaml \\
        --output-dir /workspace/data \\
        --verify-against /tmp/build_labels.csv \\
        --no-duckdb \\
    && rm /workspace/stage_data.py /workspace/inject.py /workspace/task_config.yaml \\
    && rm /tmp/build_labels.csv

RUN mkdir -p /workspace/submission
"""


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _slice_task(all_configs: list[dict], task_id: str) -> dict[str, Any]:
    for entry in all_configs:
        if entry["id"] == task_id:
            return entry
    raise KeyError(f"task {task_id} not found in task_configs.yaml")


def _build_task(
    task_root: Path,
    task_config: dict,
    *,
    regenerate_labels: bool,
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
    build_inputs = env_dir / "build_inputs"
    tests_dir = task_root / "tests"

    workspace.mkdir(parents=True, exist_ok=True)
    build_inputs.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Workspace contents (visible to the agent at runtime *until* the
    # Dockerfile rm step deletes the underscore-prefixed staging files).
    _write(workspace / "README.md", WORKSPACE_README)
    shutil.copyfile(SCRIPTS_DIR / "stage_data.py", workspace / "stage_data.py")
    shutil.copyfile(SCRIPTS_DIR / "inject.py", workspace / "inject.py")
    _write(
        workspace / "task_config.yaml",
        yaml.safe_dump(task_config, sort_keys=False),
    )

    # Tests dir: agent-hidden labels go here; verifier glue comes from the
    # canonical scripts/mimic_iv_dq harbor_evaluator copy.
    shutil.copyfile(
        SCRIPTS_DIR / "harbor_evaluator.py", tests_dir / "harbor_evaluator.py"
    )
    _write(tests_dir / "verify.py", VERIFY_PY)
    test_sh_path = tests_dir / "test.sh"
    _write(test_sh_path, TEST_SH)
    test_sh_path.chmod(0o755)

    # Labels: either generated fresh or copied from a pre-existing committed
    # file. By default we expect labels.csv to already exist alongside
    # the task config.
    labels_src = ASSETS / "labels" / f"{task_id}.csv"
    if regenerate_labels or not labels_src.exists():
        _generate_labels(task_config, labels_src)
    shutil.copyfile(labels_src, tests_dir / "labels.csv")
    # Same labels into the build context so the Dockerfile can verify.
    shutil.copyfile(labels_src, build_inputs / "labels.csv")

    # Dockerfile lives at environment/Dockerfile (matches medcli convention).
    _write(env_dir / "Dockerfile", build_dockerfile())


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
        default=REPO_ROOT / "tasks" / "mimic_iv_dq",
    )
    parser.add_argument(
        "--task-ids",
        type=str,
        default=None,
        help="Comma-separated subset (e.g. task_001,task_005). Default: all.",
    )
    parser.add_argument(
        "--regenerate-labels",
        action="store_true",
        help="Re-run corruption locally to refresh labels.csv for each task.",
    )
    args = parser.parse_args(argv)

    all_configs = yaml.safe_load(TASK_CONFIGS_PATH.read_text())["tasks"]

    if args.task_ids:
        wanted = {tid.strip() for tid in args.task_ids.split(",") if tid.strip()}
        all_configs = [c for c in all_configs if c["id"] in wanted]

    args.output_root.mkdir(parents=True, exist_ok=True)
    _write(
        args.output_root / "README.md",
        "Generated by `scripts/mimic_iv_dq/generate_harbor_tasks.py`.\n"
        "Each `task_NNN/` subdirectory is a complete Harbor task. "
        "See `scripts/mimic_iv_dq/README.md` for benchmark details.\n",
    )

    for cfg in all_configs:
        task_root = args.output_root / cfg["id"]
        print(f"Generating {task_root}", flush=True)
        _build_task(task_root, cfg, regenerate_labels=args.regenerate_labels)


if __name__ == "__main__":
    main()
