#!/usr/bin/env python3
"""Generate Harbor meta-task for EHRSQL benchmark.

This script takes raw EHRSQL JSON tasks and generates a complete Harbor meta-task
artifact suitable for agent execution and evaluation.

Usage:
    python scripts/ehrsql/generate_harbor_tasks.py \
      --output-root harbor_tasks/ehrsql \
      [--valid-json data/ehrsql/mimic_iii/valid.json data/ehrsql/eicu/valid.json ...] \
      [--test-json data/ehrsql/mimic_iii/test.json data/ehrsql/eicu/test.json ...] \
      [--selected-task-ids task_id1,task_id2 ...]
"""

from __future__ import annotations

import argparse
import json
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


def _generate_dockerfile(env_dir: Path) -> None:
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

# Set working directory
WORKDIR /workspace

# Copy workspace files (build context is harbor_tasks/ehrsql/)
COPY environment/workspace/ /workspace/

# Copy tests directory (verifier and evaluator)
COPY tests/ /tests/

# Ensure scripts are executable
RUN chmod +x /workspace/scripts/primitives/*.py || true
RUN chmod +x /tests/test.sh || true

# Make logs directory
RUN mkdir -p /logs/verifier

# Default command (agent will be started by Harbor)
CMD ["/bin/bash"]
""")


def _generate_docker_compose(env_dir: Path) -> None:
    """Generate docker-compose.yaml for local EHRSQL Harbor environment.

    Build context is set to .. (harbor_tasks/ehrsql/) so Dockerfile can
    access both environment/ and tests/ directories.
    """
    (env_dir / "docker-compose.yaml").write_text("""services:
  main:
    build:
      context: ..                    # Build from harbor_tasks/ehrsql/
      dockerfile: environment/Dockerfile
    volumes:
      - /data/ehrsql:/data/ehrsql:ro  # Mount SQLite databases (read-only)
    environment:
      - PYTHONUNBUFFERED=1
""")


def _generate_workspace_readme(workspace_dir: Path) -> None:
    """Generate README for agent workspace."""
    (workspace_dir / "README.md").write_text("""# EHRSQL Workspace

This workspace contains tools and data for SQL-based question answering over EHR databases.

## Available Tools

### `inspect_schema.py`
Inspect the database schema to understand available tables and columns.

```bash
python scripts/primitives/inspect_schema.py --db-id mimic_iii
python scripts/primitives/inspect_schema.py --db-id mimic_iii --table patient
```

### `execute_sql.py`
Execute SQL queries and retrieve results.

```bash
python scripts/primitives/execute_sql.py \\
  --db-id mimic_iii \\
  --query "SELECT * FROM patient LIMIT 5"
```

## Databases

- **MIMIC-III** (db_id: mimic_iii) — 17 tables with ICU patient data
- **eICU** (db_id: eicu) — 10 tables with multi-center ICU data

## Submission Format

Edit `submission.json` with your SQL answers:

```json
[
  {
    "task_id": "ehrsql_mimic_iii_valid_123",
    "instruction": "What is the method of intake...",
    "final_answer": "SELECT DISTINCT route FROM prescriptions WHERE drug = '...'",
    "payload": null
  }
]
```

## Workflow

1. Read the task instruction
2. Use `inspect_schema.py` to explore the database
3. Write SQL queries using `execute_sql.py` to test
4. Record final SQL in `submission.json` under `final_answer`
5. For unanswerable questions, set `final_answer` to `"null"`

Good luck! 🚀
""")


def _generate_instruction_md() -> str:
    """Generate instruction.md for agent."""
    return """# EHRSQL Benchmark - Text-to-SQL Question Answering

## Overview

Your task is to answer natural language questions about Electronic Health Records (EHR) by generating SQL queries.
The EHR databases include structured clinical data such as patients, diagnoses, medications, lab results, and vital signs.

## Databases

You have access to two EHR databases:
- **MIMIC-III**: A large, single-center database of adult ICU patients (Beth Israel Deaconess Medical Center, 2001-2012)
- **eICU**: A collaborative, multi-center database of ICU patients (Philips eICU Research Institute, 2014-2015)

Each database contains 10-17 tables with clinical events, patient demographics, and laboratory measurements.

## Tools Available

You have access to the following tools:

### `inspect_schema.py`
Inspect the database schema to understand available tables and columns.

Usage:
```bash
python scripts/primitives/inspect_schema.py --db-id mimic_iii [--table patient]
```

Outputs:
- All tables (no args) or specific table schema (with --table)
- Column names, types, and sample values

### `execute_sql.py`
Execute a SQL query against the database and retrieve results.

Usage:
```bash
python scripts/primitives/execute_sql.py --db-id mimic_iii --query "SELECT * FROM patient LIMIT 5"
```

Outputs:
- Result rows as JSON
- Execution time and row count
- SQL errors if query is invalid

## Task Format

Your tasks are in `/workspace/benchmark_tasks.json`. This file contains an array of task objects with this structure:

```json
{
  "task_id": "ehrsql_mimic_iii_valid_xyz",
  "instruction": "What is the method of intake for clobetasol propionate 0.05% ointment?\\n\\nDatabase: MIMIC-III",
  "final_answer": "",
  "payload": null
}
```

- `task_id`: Unique identifier for this task
- `instruction`: The natural language question to answer (includes database name)
- `final_answer`: You must fill this with your SQL query or "null"
- `payload`: Leave as null (for compatibility)

Process all tasks in `/workspace/benchmark_tasks.json` by:
1. Reading the JSON file to load all tasks
2. For each task, extract the `instruction` (which contains the natural language question and database name)
3. Generate your SQL answer using the schema inspection and SQL execution tools
4. Update each task object's `final_answer` field with your SQL query or "null"
5. Save the completed array back to `/workspace/submission.json` when finished

Work through as many tasks as possible within the available time.

## Workflow

1. **Load all tasks**: Read `/workspace/benchmark_tasks.json` into memory
2. **For each task**:
   - Extract the database ID (e.g., "mimic_iii" or "eicu") from the instruction
   - Parse the natural language question
   - Use `inspect_schema.py` to understand available tables/columns for that database
   - Develop SQL queries to answer the question
   - Test execution with `execute_sql.py`
   - Record your final SQL query (or "null" if unanswerable) in `final_answer`
3. **Save submission**: Write all completed tasks to `/workspace/submission.json`

## Answer Format

- **For answerable questions**: Return the final SQL query as a string
- **For unanswerable questions**: Return the string `"null"`

Example submission.json entry:
```json
{
  "task_id": "ehrsql_mimic_iii_valid_123",
  "instruction": "What is the method of intake for clobetasol propionate 0.05% ointment?",
  "final_answer": "SELECT DISTINCT route FROM prescriptions WHERE drug = 'clobetasol propionate 0.05% ointment'",
  "payload": null
}
```

## Tips

- Start by exploring the schema with `inspect_schema.py` to understand available data
- Use `LIMIT` clauses when testing queries to avoid excessive output
- SQL syntax: Standard SQL (SQLite dialect for both databases)
- Time reference: Database records are shifted to 2100-2105 for de-identification
- For temporal queries, use the shifted dates (not current dates)

## Evaluation

Your submission will be evaluated by:
1. Executing your SQL query against the live database
2. Comparing your result set to the gold standard SQL result
3. Measuring execution accuracy: did you get the correct answer?
4. Measuring answerability: did you correctly identify unanswerable questions?

Good luck!
"""


def _generate_primitive_scripts(workspace_dir: Path) -> None:
    """Generate SQL execution primitive scripts in workspace/scripts/primitives/."""
    scripts_dir = workspace_dir / "scripts" / "primitives"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # inspect_schema.py
    (scripts_dir / "inspect_schema.py").write_text("""#!/usr/bin/env python3
\"\"\"Inspect database schema for EHRSQL tasks.\"\"\"
import argparse
import json
import sqlite3
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-id", required=True, choices=["mimic_iii", "eicu"])
    parser.add_argument("--table", help="Specific table name to inspect")
    args = parser.parse_args()

    db_dir = Path("/data/ehrsql") / args.db_id
    db_file = db_dir / f"{args.db_id}.sqlite"

    if not db_file.exists():
        print(f"Error: Database file not found: {db_file}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    try:
        if args.table:
            # Show schema for specific table
            cursor.execute(f"PRAGMA table_info({args.table})")
            columns = cursor.fetchall()
            print(f"Table: {args.table}")
            print(f"{'Column':<30} {'Type':<20}")
            print("-" * 50)
            for col_id, col_name, col_type, notnull, dflt, pk in columns:
                print(f"{col_name:<30} {col_type:<20}")

            # Show sample row
            cursor.execute(f"SELECT * FROM {args.table} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"\\nSample row: {sample}")
        else:
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Database: {args.db_id}")
            print(f"Tables ({len(tables)}):")
            for table in sorted(tables):
                print(f"  - {table}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
""")

    # execute_sql.py
    (scripts_dir / "execute_sql.py").write_text("""#!/usr/bin/env python3
\"\"\"Execute SQL queries against EHRSQL databases.\"\"\"
import argparse
import json
import sqlite3
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-id", required=True, choices=["mimic_iii", "eicu"])
    parser.add_argument("--query", required=True, help="SQL query to execute")
    parser.add_argument("--timeout", type=int, default=30, help="Query timeout in seconds")
    args = parser.parse_args()

    db_dir = Path("/data/ehrsql") / args.db_id
    db_file = db_dir / f"{args.db_id}.sqlite"

    if not db_file.exists():
        print(f"Error: Database file not found: {db_file}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_file))
    conn.timeout = args.timeout

    try:
        cursor = conn.cursor()
        cursor.execute(args.query)
        rows = cursor.fetchall()

        # Get column names
        col_names = [desc[0] for desc in cursor.description] if cursor.description else []

        # Format results as list of dicts
        results = [dict(zip(col_names, row)) for row in rows]

        # Output JSON
        output = {
            "status": "success",
            "row_count": len(results),
            "columns": col_names,
            "rows": results,
        }
        print(json.dumps(output, indent=2))
    except sqlite3.Error as e:
        output = {
            "status": "error",
            "error": str(e),
        }
        print(json.dumps(output, indent=2), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
""")


def generate_harbor_task(
    *,
    output_root: Path,
    raw_tasks: list[dict[str, Any]] | None = None,
    selected_task_ids: list[str] | None = None,
    sample_size: int = 200,
) -> None:
    """Generate complete Harbor meta-task for EHRSQL.

    Args:
        output_root: Root directory for generated Harbor task
        raw_tasks: List of raw EHRSQL tasks (will load defaults if None)
        selected_task_ids: Task IDs to include (will select defaults if None).
                          If provided, uses exactly these tasks (no re-selection).
        sample_size: Number of tasks to select if using default strategy (default 200)
    """
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    # Load tasks if not provided
    if raw_tasks is None:
        repo_root = Path(__file__).parent.parent.parent
        data_dir = repo_root / "data" / "ehrsql"
        valid_paths = [
            data_dir / "mimic_iii" / "valid.json",
            data_dir / "eicu" / "valid.json",
        ]
        raw_tasks = _load_all_tasks(valid_paths=valid_paths)

    # Select tasks if not provided
    # Only apply default selection if selected_task_ids is still None
    # (it would have been populated by main() if user provided JSON files)
    if selected_task_ids is None:
        selected_task_ids = default_selected_task_ids(raw_tasks, sample_size=sample_size)

    selected_tasks = select_tasks(raw_tasks, selected_task_ids)

    # Generate public benchmark_tasks
    benchmark_tasks = _generate_benchmark_tasks(selected_tasks)

    # Generate hidden answer keys
    answer_key = _generate_answer_key(selected_tasks)

    # Generate submission template
    submission_template = _create_submission_template(benchmark_tasks)

    # Write files
    (output_root / "task.toml").write_text(
        _generate_task_toml(output_root, selected_task_ids, len(selected_tasks))
    )

    (output_root / "instruction.md").write_text(_generate_instruction_md())

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

    # Generate primitive scripts
    _generate_primitive_scripts(workspace_dir)

    # Create tests directory
    tests_dir = output_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    (tests_dir / "task_answer_key.json").write_text(
        json.dumps(answer_key, indent=2)
    )

    # Copy evaluator and verifier modules to make harbor_tasks self-contained
    _copy_evaluator_module(tests_dir)
    _copy_verifier_script(tests_dir)
    _generate_test_script(tests_dir)

    # Generate Dockerfile and docker-compose
    _generate_dockerfile(env_dir)
    _generate_docker_compose(env_dir)
    _generate_workspace_readme(workspace_dir)

    print(f"✓ Generated Harbor meta-task at {output_root}")
    print(f"  - {len(selected_tasks)} tasks selected")
    print(f"  - task.toml, instruction.md, benchmark_tasks.json created")
    print(f"  - workspace/ with submission template, primitives, and README")
    print(f"  - environment/ with Dockerfile and docker-compose")
    print(f"  - tests/ with answer key and evaluator module")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Harbor meta-task for EHRSQL benchmark"
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Root directory for generated Harbor task",
    )
    parser.add_argument(
        "--valid-json",
        nargs="+",
        help="Path(s) to EHRSQL valid.json files (uses ALL tasks from these files)",
    )
    parser.add_argument(
        "--test-json",
        nargs="+",
        help="Path(s) to EHRSQL test.json files (uses ALL tasks from these files)",
    )
    parser.add_argument(
        "--selected-task-ids",
        help="Comma-separated task IDs to include (overrides default/file selection)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=200,
        help="Number of tasks to select with default strategy (default 200)",
    )

    args = parser.parse_args()

    # Load tasks
    valid_paths = [Path(p) for p in (args.valid_json or [])]
    test_paths = [Path(p) for p in (args.test_json or [])]

    raw_tasks = _load_all_tasks(valid_paths=valid_paths, test_paths=test_paths)

    # Parse selected task IDs
    # If user specifies --selected-task-ids, use those
    # Otherwise, if user specifies JSON files, use ALL tasks from them
    # Otherwise, use default strategy (8 representative tasks)
    selected_task_ids = None
    if args.selected_task_ids:
        selected_task_ids = args.selected_task_ids.split(",")
    elif valid_paths or test_paths:
        # User provided JSON files, so use ALL tasks from them (don't apply default selection)
        selected_task_ids = [t.get("id") for t in raw_tasks if t.get("id")]

    # Generate
    generate_harbor_task(
        output_root=Path(args.output_root),
        raw_tasks=raw_tasks if (valid_paths or test_paths) else None,
        selected_task_ids=selected_task_ids,
        sample_size=args.sample_size,
    )


if __name__ == "__main__":
    main()
