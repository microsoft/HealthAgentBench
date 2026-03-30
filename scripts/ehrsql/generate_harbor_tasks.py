#!/usr/bin/env python3
"""Generate Harbor meta-task for EHRSQL benchmark.

This script takes raw EHRSQL JSON tasks and generates a complete Harbor meta-task
artifact suitable for agent execution and evaluation.

Sampling Strategy:
- With --valid-json or --test-json: Randomly samples tasks from provided JSON files
- Without JSON files: Uses default strategy (stratified sampling by database/importance)
- With --selected-task-ids: Uses exact task IDs (no sampling)

Splitting Strategy:
- With --split_task_by_n N: Creates N worker subdirectories (worker_0, worker_1, ..., worker_{N-1})
  Tasks are shuffled (deterministically, with seed=42) before splitting to balance difficulty across workers.
  Each worker then gets a sequential chunk of the shuffled tasks.
  Useful for parallel execution via Harbor with n_concurrent_trials=N.

Usage (random sample 100 tasks from mimic_iii validation set):
    python scripts/ehrsql/generate_harbor_tasks.py \
      --output-root tasks/mimic_iii_valid \
      --valid-json scripts/ehrsql/assets/mimic_iii/valid.json \
      --sample-size 100

Usage (specific task IDs):
    python scripts/ehrsql/generate_harbor_tasks.py \
      --output-root tasks/ehrsql \
      --valid-json scripts/ehrsql/assets/mimic_iii/valid.json \
      --selected-task-ids task_id1,task_id2,task_id3

Usage (default strategy - 200 stratified tasks):
    python scripts/ehrsql/generate_harbor_tasks.py \
      --output-root tasks/ehrsql

Usage (split into 10 parallel workers):
    python scripts/ehrsql/generate_harbor_tasks.py \
      --output-root tasks/ehrsql/ehrsql_mimic_iii_valid \
      --valid-json scripts/ehrsql/assets/mimic_iii/valid.json \
      --split_task_by_n 10
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
from pathlib import Path
from typing import Any

from normalization import (
    build_harbor_answer_key,
    build_instruction,
    default_selected_task_ids,
    infer_db_id,
    infer_split,
    load_raw_tasks,
    normalize_harbor_task,
    select_tasks,
)


def _load_all_tasks(
    valid_paths: list[Path] | None = None,
    test_paths: list[Path] | None = None,
) -> list[dict[str, Any]]:
    """Load all EHRSQL tasks from specified paths."""
    all_tasks = []

    if valid_paths:
        for path in valid_paths:
            tasks = load_raw_tasks(path)
            for task in tasks:
                task["split"] = "valid"
            all_tasks.extend(tasks)

    if test_paths:
        for path in test_paths:
            tasks = load_raw_tasks(path)
            for task in tasks:
                task["split"] = "test"
            all_tasks.extend(tasks)

    return all_tasks


def _generate_benchmark_tasks(
    raw_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate public benchmark_tasks.json rows (agent-visible).

    Args:
        raw_tasks: Raw EHRSQL tasks

    Returns:
        List of Harbor task dicts
    """
    return [
        normalize_harbor_task(task, split=infer_split(task))
        for task in raw_tasks
    ]


def _generate_answer_key(
    raw_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate hidden answer key rows (verifier-only).

    Args:
        raw_tasks: Raw EHRSQL tasks

    Returns:
        List of answer key dicts
    """
    return [
        build_harbor_answer_key(task, split=infer_split(task))
        for task in raw_tasks
    ]


def _create_submission_template(benchmark_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create submission template for agent to fill in.

    Args:
        benchmark_tasks: Public benchmark tasks

    Returns:
        Submission template (copy with empty final_answer fields)
    """
    return [
        {
            "task_id": task["task_id"],
            "instruction": task["instruction"],
            "final_answer": "",
            "payload": None,
        }
        for task in benchmark_tasks
    ]


def _generate_task_toml(
    output_root: Path,
    selected_task_ids: list[str],
    num_tasks: int,
) -> str:
    """Generate task.toml configuration."""
    return f"""version = "1.0"

[metadata]
benchmark = "ehrsql"
mode = "meta-task"
description = "Text-to-SQL question answering over MIMIC-III and eICU EHR databases"
selected_task_ids = {selected_task_ids}
num_tasks = {num_tasks}
submission_path = "/workspace/submission.json"

[verifier]
timeout_sec = 1800.0

[agent]
timeout_sec = 3600.0

[environment]
build_timeout_sec = 1800.0
allow_internet = true
cpus = 2
memory_mb = 4096
storage_mb = 20480
gpus = 0
mcp_servers = []
"""


def _copy_evaluator_module(tests_dir: Path) -> None:
    """Copy evaluator module into harbor_tasks for self-containment."""
    # Read the evaluator from scripts/ehrsql/harbor_evaluator.py
    evaluator_src = Path(__file__).parent / "harbor_evaluator.py"

    if evaluator_src.exists():
        evaluator_code = evaluator_src.read_text()
        (tests_dir / "evaluator.py").write_text(evaluator_code)


def _copy_verifier_script(tests_dir: Path) -> None:
    """Copy verifier script into harbor_tasks for self-containment."""
    # Read the verifier from scripts/ehrsql/verify_meta_task.py
    verifier_src = Path(__file__).parent / "verify_meta_task.py"

    if verifier_src.exists():
        verifier_code = verifier_src.read_text()
        (tests_dir / "verify_meta_task.py").write_text(verifier_code)


def _generate_stub_verifier(tests_dir: Path) -> None:
    """Generate a minimal verifier that always passes (skips SQL evaluation)."""
    (tests_dir / "verify_meta_task.py").write_text("""#!/usr/bin/env python3
\"\"\"Stub verifier — always passes. Use aggregate_worker_submissions.py for evaluation.\"\"\"
import json
from pathlib import Path

submission = json.loads(Path("/workspace/submission.json").read_text())
filled = sum(1 for r in submission if r.get("final_answer", "").strip())
total = len(submission)

logs = Path("/logs/verifier")
logs.mkdir(parents=True, exist_ok=True)

reward = filled / total if total else 0.0
(logs / "reward.txt").write_text(str(reward))
(logs / "meta_results.json").write_text(json.dumps({
    "status": "success",
    "pass_at_1": reward,
    "total_tasks": total,
    "filled_tasks": filled,
    "note": "stub verifier — fill rate only, no SQL evaluation"
}))
(logs / "submission.json").write_text(json.dumps(submission, indent=2))
print(f"Stub verifier: {filled}/{total} filled ({reward:.1%})")
""")


def _generate_test_script(tests_dir: Path) -> None:
    """Generate test.sh script that Harbor calls to run the verifier."""
    (tests_dir / "test.sh").write_text("""#!/bin/bash
# Harbor test script for EHRSQL verification

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

# Run the verifier
python verify_meta_task.py
""")
    # Make executable
    (tests_dir / "test.sh").chmod(0o755)


def _generate_dockerfile(env_dir: Path, db_id: str) -> None:
    """Generate Dockerfile for EHRSQL Harbor environment.

    Note: Build context should be harbor_tasks/ehrsql/ (parent directory)
    not environment/, so COPY can access both environment/ and tests/
    """
    (env_dir / "Dockerfile").write_text("""FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    bash \\
    curl \\
    jq \\
    sqlite3 \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies required for evaluation
RUN pip install --no-cache-dir \\
    func-timeout>=4.3.5 \\
    numpy>=2.4.2

# Set working directory
WORKDIR /workspace

# Copy workspace files (build context is harbor_tasks/ehrsql/)
COPY environment/workspace/ /workspace/

# DO NOT copy /tests directory (answer keys will be mounted at runtime by Harbor)
# This prevents agent from accessing the answer key file during task execution
# Harbor will mount tests/ directory for the verifier only

# Make logs directory
RUN mkdir -p /logs/verifier

# Default command (agent will be started by Harbor)
CMD ["/bin/bash"]
""")


def _generate_docker_compose(env_dir: Path, db_id: str) -> None:
    """Generate docker-compose.yaml for local EHRSQL Harbor environment.

    Build context is set to .. (tasks/ehrsql/) so Dockerfile can
    access both environment/ and tests/ directories.
    """
    # Get absolute path to data directory (resolve symlinks)
    repo_root = Path(__file__).parent.parent.parent
    db_dir = (repo_root / "scripts" / "ehrsql" / "assets" / db_id).resolve()

    (env_dir / "docker-compose.yaml").write_text(f"""services:
  main:
    build:
      context: ..                    # Build from harbor_tasks/ehrsql/
      dockerfile: environment/Dockerfile
    volumes:
      - {db_dir}:/data/ehrsql/{db_id}:ro  # Mount {db_id} SQLite database (read-only)
    environment:
      - PYTHONUNBUFFERED=1
    # Resource limits for safe local testing
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
""")


def _generate_workspace_readme(workspace_dir: Path, db_id: str) -> None:
    """Generate README for agent workspace."""
    db_name = _DB_DISPLAY_NAMES.get(db_id, db_id)
    db_path = f"/data/ehrsql/{db_id}/{db_id}.sqlite"
    (workspace_dir / "README.md").write_text(f"""# Workspace Files

- `benchmark_tasks.json`: task definitions for SQL generation
- `submission.json`: editable task rows; fill in `final_answer` (SQL query or "null")

SQLite database:
- {db_name}: `{db_path}`

The verifier reads `/workspace/submission.json` after the agent stops.
""")


_DB_DISPLAY_NAMES = {
    "mimic_iii": "MIMIC-III",
    "eicu": "eICU",
}


def _generate_instruction_md(db_id: str) -> str:
    """Generate database-specific instruction.md for agent."""
    db_name = _DB_DISPLAY_NAMES.get(db_id, db_id)
    db_path = f"/data/ehrsql/{db_id}/{db_id}.sqlite"

    return f"""# EHRSQL: Text-to-SQL over EHR Data

You are working inside a task environment that contains:

- a {db_name} SQLite EHR database at `{db_path}`
- task descriptions at `/workspace/benchmark_tasks.json`
- editable task rows already prepared at `/workspace/submission.json`

Your final work product is `/workspace/submission.json`.

## Your Task

Process every row in `/workspace/submission.json`. For each row:

1. Read the task instruction
2. Answer the question from the instruction with a SQL query or "null" if unanswerable
3. Write your answer into the `final_answer` field of the same row in `/workspace/submission.json`

**You must complete all rows before stopping.**

## Submission Rules

- Each row has fields: `task_id`, `instruction`, `final_answer`
- Set `final_answer` to: a valid SQL query (answerable) OR the string `"null"` (unanswerable)
- Do NOT modify `task_id`, `instruction`, or `payload` fields
- Work autonomously until all rows are complete

## Important: Work Independently

- **Do not ask for user feedback, approval, or permission** to continue
- **Do not ask to reprioritize tasks or wait for input**
- You have all information needed: database, schema, task instructions
- Work continuously until every row in the submission is filled
- You will not receive responses to requests for user input

## Benchmark Integrity

- Do not download EHRSQL datasets from external sources
- Do not copy or look up answers online
- Generate all SQL based on your own schema inspection and database experiments

## Database

- {db_name}: `{db_path}`
"""


def _split_into_chunks(items: list[Any], n: int) -> list[list[Any]]:
    """Split items into n sequential chunks deterministically.

    Args:
        items: List to split
        n: Number of chunks

    Returns:
        List of n chunks, where each chunk is items[i*size:(i+1)*size]
        The last chunk may be larger if len(items) is not divisible by n.
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    if n > len(items):
        n = len(items)

    size = len(items) // n
    chunks = []
    for i in range(n - 1):
        chunks.append(items[i * size : (i + 1) * size])
    # Last chunk gets the remainder
    chunks.append(items[(n - 1) * size :])
    return chunks


def _write_worker_task(
    worker_dir: Path,
    selected_task_ids: list[str],
    benchmark_tasks_chunk: list[dict[str, Any]],
    answer_key_chunk: list[dict[str, Any]],
    submission_template_chunk: list[dict[str, Any]],
    db_id: str,
    skip_evaluator: bool = False,
) -> None:
    """Write a complete Harbor task for one worker."""
    worker_dir.mkdir(parents=True, exist_ok=True)

    # Write task.toml (use chunk-specific task IDs, not the full list)
    chunk_task_ids = [t["task_id"] for t in benchmark_tasks_chunk]
    (worker_dir / "task.toml").write_text(
        _generate_task_toml(worker_dir, chunk_task_ids, len(benchmark_tasks_chunk))
    )

    # Write instruction.md
    (worker_dir / "instruction.md").write_text(_generate_instruction_md(db_id))

    # Write root-level benchmark_tasks.json
    (worker_dir / "benchmark_tasks.json").write_text(
        json.dumps(benchmark_tasks_chunk, indent=2)
    )

    # Create environment directory
    env_dir = worker_dir / "environment"
    env_dir.mkdir(parents=True, exist_ok=True)

    # Create workspace
    workspace_dir = env_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Write workspace submission.json
    (workspace_dir / "submission.json").write_text(
        json.dumps(submission_template_chunk, indent=2)
    )

    # Write workspace benchmark_tasks.json
    (workspace_dir / "benchmark_tasks.json").write_text(
        json.dumps(benchmark_tasks_chunk, indent=2)
    )

    # # Generate primitive scripts
    # _generate_primitive_scripts(workspace_dir)

    # Create tests directory
    tests_dir = worker_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Write worker's answer key chunk (NOT the full key — this is just for the worker's tasks)
    (tests_dir / "task_answer_key.json").write_text(
        json.dumps(answer_key_chunk, indent=2)
    )

    # Copy evaluator and verifier modules (or stub if skipped)
    if skip_evaluator:
        _generate_stub_verifier(tests_dir)
    else:
        _copy_evaluator_module(tests_dir)
        _copy_verifier_script(tests_dir)
    _generate_test_script(tests_dir)

    # Generate Dockerfile and docker-compose
    _generate_dockerfile(env_dir, db_id)
    _generate_docker_compose(env_dir, db_id)
    _generate_workspace_readme(workspace_dir, db_id)


def _generate_primitive_scripts(workspace_dir: Path) -> None:
    """Generate helper scripts for task management (medagentbench style)."""
    scripts_dir = workspace_dir / "scripts" / "primitives"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # get_row.py - retrieve a specific row from submission.json
    (scripts_dir / "get_row.py").write_text('''#!/usr/bin/env python3
"""Get a row from submission.json by index (0-indexed)."""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Get a row from submission.json by index (0-indexed)"
    )
    parser.add_argument("row_index", type=int, help="Row index (0-indexed)")
    args = parser.parse_args()

    submission_path = Path("/workspace/submission.json")
    submission = json.loads(submission_path.read_text())

    if args.row_index < 0 or args.row_index >= len(submission):
        print(f"Error: row_index {args.row_index} out of range (0-{len(submission)-1})", file=sys.stderr)
        sys.exit(1)

    row = submission[args.row_index]
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
''')
    (scripts_dir / "get_row.py").chmod(0o755)

    # set_answer.py - update final_answer for a row
    (scripts_dir / "set_answer.py").write_text('''#!/usr/bin/env python3
"""Update final_answer for a row in submission.json."""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update final_answer for a row in submission.json"
    )
    parser.add_argument("row_index", type=int, help="Row index (0-indexed)")
    parser.add_argument("answer", type=str, help="SQL query or 'null' for unanswerable")
    args = parser.parse_args()

    submission_path = Path("/workspace/submission.json")
    submission = json.loads(submission_path.read_text())

    if args.row_index < 0 or args.row_index >= len(submission):
        print(f"Error: row_index {args.row_index} out of range (0-{len(submission)-1})", file=sys.stderr)
        sys.exit(1)

    submission[args.row_index]["final_answer"] = args.answer
    submission_path.write_text(json.dumps(submission, indent=2))

    # Show progress
    answered = sum(1 for task in submission if task.get("final_answer", "").strip())
    total = len(submission)
    percent = round(100.0 * answered / total, 1)
    print(f"✓ Row {args.row_index} updated | Progress: {answered}/{total} ({percent}%)")


if __name__ == "__main__":
    main()
''')
    (scripts_dir / "set_answer.py").chmod(0o755)


def generate_harbor_task(
    *,
    output_root: Path,
    raw_tasks: list[dict[str, Any]] | None = None,
    selected_task_ids: list[str] | None = None,
    sample_size: int | None = None,
    split_task_by_n: int | None = None,
    skip_evaluator: bool = False,
) -> None:
    """Generate complete Harbor meta-task for EHRSQL, optionally split into N workers.

    Args:
        output_root: Root directory for generated Harbor task
        raw_tasks: List of raw EHRSQL tasks (will load defaults if None)
        selected_task_ids: Task IDs to include (will select defaults if None).
                          If provided, uses exactly these tasks (no re-selection).
        sample_size: Number of tasks to select if using default strategy.
                     If None (default), uses ALL available tasks.
        split_task_by_n: If provided, split the task into N worker subdirectories
                        (e.g., worker_0, worker_1, ..., worker_{N-1}).
                        Tasks are shuffled (deterministically) before splitting to balance
                        difficulty across workers. Each worker then gets a sequential chunk.
                        If None (default), generate a single task at output_root.
    """
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    # Load tasks if not provided
    if raw_tasks is None:
        repo_root = Path(__file__).parent.parent.parent
        data_dir = repo_root / "scripts" / "ehrsql" / "assets"
        valid_paths = [
            data_dir / "mimic_iii" / "valid.json",
            data_dir / "eicu" / "valid.json",
        ]
        raw_tasks = _load_all_tasks(valid_paths=valid_paths)

    # Select tasks if not provided
    # Only apply default selection if selected_task_ids is still None
    # (it would have been populated by main() if user provided JSON files)
    if selected_task_ids is None:
        # If sample_size is None, use all available tasks
        effective_sample_size = sample_size if sample_size is not None else len(raw_tasks)
        selected_task_ids = default_selected_task_ids(raw_tasks, sample_size=effective_sample_size)

    selected_tasks = select_tasks(raw_tasks, selected_task_ids)

    # Detect database from tasks
    db_ids = {t.get("db_id", "") for t in selected_tasks}
    db_ids.discard("")
    if len(db_ids) == 1:
        db_id = db_ids.pop()
    else:
        raise ValueError(
            f"Expected tasks from a single database, got: {db_ids}. "
            "Pass a single --valid-json or --test-json per database."
        )

    # Generate public benchmark_tasks
    benchmark_tasks = _generate_benchmark_tasks(selected_tasks)

    # Generate hidden answer keys
    answer_key = _generate_answer_key(selected_tasks)

    # Generate submission template
    submission_template = _create_submission_template(benchmark_tasks)

    # If split_task_by_n is provided, create N worker tasks
    if split_task_by_n and split_task_by_n > 1:
        # Shuffle tasks before splitting to balance difficulty across workers
        # Create shuffled indices using deterministic seed
        indices = list(range(len(benchmark_tasks)))
        random.Random(42).shuffle(indices)

        # Apply same permutation to all three lists (keep them aligned)
        benchmark_tasks = [benchmark_tasks[i] for i in indices]
        answer_key = [answer_key[i] for i in indices]
        submission_template = [submission_template[i] for i in indices]

        # Split data into N chunks
        benchmark_chunks = _split_into_chunks(benchmark_tasks, split_task_by_n)
        answer_key_chunks = _split_into_chunks(answer_key, split_task_by_n)
        submission_chunks = _split_into_chunks(submission_template, split_task_by_n)

        # Create N worker task directories
        for i in range(len(benchmark_chunks)):
            worker_dir = output_root / f"worker_{i}"
            _write_worker_task(
                worker_dir,
                selected_task_ids,  # Original task IDs for task.toml
                benchmark_chunks[i],
                answer_key_chunks[i],
                submission_chunks[i],
                db_id,
                skip_evaluator=skip_evaluator,
            )

        print(f"✓ Generated {len(benchmark_chunks)} worker tasks at {output_root}")
        for i, bm_chunk in enumerate(benchmark_chunks):
            print(f"  - worker_{i}/: {len(bm_chunk)} tasks")
        print(f"  Total: {len(benchmark_tasks)} tasks split into {len(benchmark_chunks)} workers")
    else:
        # Single task (no splitting)
        # Write files
        (output_root / "task.toml").write_text(
            _generate_task_toml(output_root, selected_task_ids, len(selected_tasks))
        )

        (output_root / "instruction.md").write_text(_generate_instruction_md(db_id))

        (output_root / "benchmark_tasks.json").write_text(
            json.dumps(benchmark_tasks, indent=2)
        )

        # Create environment directory
        env_dir = output_root / "environment"
        env_dir.mkdir(parents=True, exist_ok=True)

        # Create workspace
        workspace_dir = env_dir / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        (workspace_dir / "submission.json").write_text(
            json.dumps(submission_template, indent=2)
        )

        (workspace_dir / "benchmark_tasks.json").write_text(
            json.dumps(benchmark_tasks, indent=2)
        )

        # # Generate primitive scripts
        # _generate_primitive_scripts(workspace_dir)

        # Create tests directory
        tests_dir = output_root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        (tests_dir / "task_answer_key.json").write_text(
            json.dumps(answer_key, indent=2)
        )

        # Copy evaluator and verifier modules (or stub if skipped)
        if skip_evaluator:
            _generate_stub_verifier(tests_dir)
        else:
            _copy_evaluator_module(tests_dir)
            _copy_verifier_script(tests_dir)
        _generate_test_script(tests_dir)

        # Generate Dockerfile and docker-compose
        _generate_dockerfile(env_dir, db_id)
        _generate_docker_compose(env_dir, db_id)
        _generate_workspace_readme(workspace_dir, db_id)

        print(f"✓ Generated Harbor meta-task at {output_root}")
        print(f"  - {len(selected_tasks)} tasks selected")
        print(f"  - task.toml, instruction.md, benchmark_tasks.json created")
        print(f"  - workspace/ with submission template and README (minimal, no tools)")
        print(f"  - environment/ with Dockerfile and docker-compose")
        print(f"  - tests/ with answer key and evaluator module")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Harbor meta-task for EHRSQL benchmark"
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Root directory for generated Harbor task artifacts",
    )
    parser.add_argument(
        "--valid-json",
        nargs="+",
        help="Path(s) to EHRSQL valid.json files. Tasks are sampled using --sample-size (or all if --selected-task-ids provided)",
    )
    parser.add_argument(
        "--test-json",
        nargs="+",
        help="Path(s) to EHRSQL test.json files. Tasks are sampled using --sample-size (or all if --selected-task-ids provided)",
    )
    parser.add_argument(
        "--selected-task-ids",
        help="Comma-separated task IDs to include (overrides default/file selection)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of tasks to randomly sample (default: all available tasks)",
    )
    parser.add_argument(
        "--split_task_by_n",
        type=int,
        default=None,
        help="If provided, split the task into N worker subdirectories (worker_0, worker_1, ..., worker_{N-1}). Each worker gets a sequential, deterministic chunk of tasks. Useful for parallel execution.",
    )
    parser.add_argument(
        "--skip-evaluator",
        action="store_true",
        help="Skip copying evaluator/verifier into each worker (saves ~20K per worker). Use aggregate_worker_submissions.py for post-run evaluation instead.",
    )

    args = parser.parse_args()

    # Load tasks from specified paths
    valid_paths = [Path(p) for p in (args.valid_json or [])]
    test_paths = [Path(p) for p in (args.test_json or [])]

    # Parse selected task IDs
    selected_task_ids = None
    if args.selected_task_ids:
        selected_task_ids = args.selected_task_ids.split(",")

    # Load tasks and determine sampling strategy
    raw_tasks = None
    if valid_paths or test_paths:
        # User provided JSON files: load from them and apply sampling
        raw_tasks = _load_all_tasks(valid_paths=valid_paths, test_paths=test_paths)
        # If no explicit task IDs specified, apply sampling (uses default_selected_task_ids which is now random)
        if selected_task_ids is None:
            # If sample_size is None, use all available tasks
            effective_sample_size = args.sample_size if args.sample_size is not None else len(raw_tasks)
            selected_task_ids = default_selected_task_ids(raw_tasks, sample_size=effective_sample_size)
    else:
        # No JSON files provided: use default behavior (generate_harbor_task will load defaults)
        selected_task_ids = None

    # Generate
    generate_harbor_task(
        output_root=Path(args.output_root),
        raw_tasks=raw_tasks,
        selected_task_ids=selected_task_ids,
        sample_size=args.sample_size,
        split_task_by_n=args.split_task_by_n,
        skip_evaluator=args.skip_evaluator,
    )


if __name__ == "__main__":
    main()
