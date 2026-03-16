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
    # Get absolute path to data directory (resolve symlinks)
    repo_root = Path(__file__).parent.parent.parent
    db_dir = (repo_root / "data" / "ehrsql").resolve()

    (env_dir / "docker-compose.yaml").write_text(f"""services:
  main:
    build:
      context: ..                    # Build from harbor_tasks/ehrsql/
      dockerfile: environment/Dockerfile
    volumes:
      - {db_dir}:/data/ehrsql:ro  # Mount SQLite databases (read-only)
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

You are working inside a task environment that contains:
- Two EHR databases: **MIMIC-III** and **eICU**
- Task descriptions at `/workspace/benchmark_tasks.json`
- Editable task rows at `/workspace/submission.json`
- Primitive SQL helper scripts under `/workspace/scripts/primitives/` (use `--help` to learn)

## Your Task

**Your final work product is `/workspace/submission.json`.**

You must complete **every single row** in this file. Each row is one SQL generation task:
1. Read the `instruction` (a natural language question about EHR data)
2. Generate a SQL query that answers it (or the string "null" if unanswerable)
3. Write your answer to `final_answer`
4. Move to the next row
5. **Stop when every row is complete**

## Suggested Workflow

1. **Count your tasks**: Load `/workspace/benchmark_tasks.json` to see how many rows you need to complete
2. **For each task** (process in order, one at a time):
   - Read the `instruction` field and extract the database name (`MIMIC-III` or `eICU`)
   - Start by reading the database-specific cheat sheet:
     `python scripts/primitives/schema_notes.py --db-id mimic_iii`
   - If a lab, diagnosis, procedure, medication, or treatment name is mentioned, find its actual table/value mapping before writing SQL:
     `python scripts/primitives/find_text_matches.py --db-id mimic_iii --keyword "hematocrit"`
   - Use `python scripts/primitives/inspect_schema.py --db-id mimic_iii --table admissions` only after you know which table is relevant
   - Develop the SQL query only after confirming the relevant table, join path, and filter values
   - Test the SQL with `python scripts/primitives/execute_sql.py --db-id mimic_iii --query "SELECT ..."`
   - Write the final SQL query (or the string "null") in `final_answer`
   - Update and save `/workspace/submission.json`
3. **Track progress**: Print "Task X/N completed" periodically so you know how many remain
4. **Complete all tasks**: When you have filled `final_answer` for every single row, confirm you are done

## High-Value Rules

1. **Never guess codes, item IDs, or table names from memory.** Derive them from lookup tables or the keyword search helper.
2. **Match the question's grain exactly.** If the question asks for the first event, return the first event row, not an aggregate unless the aggregate is explicitly requested.
3. **Use the patient identity model of the database correctly.**
   - In **MIMIC-III**, start from `patients.subject_id`, then usually go through `admissions.hadm_id`, and for ICU event tables go through `icustays.icustay_id`.
   - In **eICU**, many questions start from `patient.uniquepid`, then move to one or more `patient.patientunitstayid` rows.
4. **Prefer lookup-by-name over hard-coded IDs.**
   - MIMIC-III: use `d_labitems`, `d_items`, `d_icd_diagnoses`, and `d_icd_procedures`
   - eICU: search text columns in `diagnosis`, `medication`, `treatment`, `lab`, or `allergy`
5. **Return `"null"` only when the question truly asks for unsupported knowledge.**
   - Good `"null"` cases: recommendation or advice ("what should I do"), future treatment suggestion ("what drug can be prescribed"), or facts with no represented field
   - Bad `"null"` cases: the data likely exists but needs a different join path or broader table search

## Database Notes

### MIMIC-III quick map

- `admissions`: hospital visits, admission/discharge times, admission source
- `icustays`: ICU stays linked to admissions
- `transfers`: care unit movement history; use this for care-unit questions
- `labevents` + `d_labitems`: lab measurements and their names
- `chartevents` + `d_items`: bedside observations and item labels
- `inputevents_cv` / `outputevents`: ICU intake and output events
- `prescriptions`: medication orders
- `microbiologyevents`: specimen and microbiology tests
- `diagnoses_icd` + `d_icd_diagnoses`: diagnoses and their descriptions
- `procedures_icd` + `d_icd_procedures`: procedures and their descriptions
- `cost`: cost rows linked by `hadm_id` or event IDs

### eICU quick map

- `patient`: admission, discharge, demographics, weights, stay identifiers
- `diagnosis`: diagnosis strings and timing
- `medication`: medication orders and drug names
- `lab`: lab names, results, and collection times
- `intakeoutput`: intake/output events and amounts
- `treatment`: treatment strings and timing
- `vitalperiodic`: time-series vital signs
- `cost`: hospital cost data
- `allergy`: allergy and adverse reaction text
- `microlab`: microbiology results

## Query Design Patterns

- For "first", "last", or "current" questions, identify the exact event timestamp column and order by it.
- For "same hospital visit" questions, join through the encounter identifier (`hadm_id` in MIMIC-III, stay identifiers in eICU) before applying temporal filters.
- For "same month", "last year", or "within N months" questions, anchor the time window to the event described in the question, not to the global maximum timestamp unless the question says "latest" or "current".
- For yes/no questions, return a SQL expression that yields a boolean-like result from the database, but only if the underlying event is represented in the schema.
- When a phrase sounds clinical but not obviously stored as a structured field, search the text-bearing tables first instead of inventing a code.

## Submission Rules

- Edit `/workspace/submission.json` — a JSON array of task objects
- For each task, set **exactly two** editable fields:
  - `final_answer`: Either a SQL query string OR the literal string `"null"`
  - `payload`: Leave as `null` (for compatibility)
- Do NOT add new fields, skip rows, or modify other fields

## Answer Format - CRITICAL

**These are NOT the same:**
- ✓ CORRECT for answerable: `"SELECT * FROM table"` (a SQL query string)
- ✓ CORRECT for unanswerable: `"null"` (exactly 4 characters: n-u-l-l)
- ✗ WRONG: Empty string `""` or blank field — this will be scored as an error
- ✗ WRONG: `null` without quotes (JSON null value) — must be the string `"null"`

Example correct submission entries:
```json
{
  "task_id": "ehrsql_mimic_iii_valid_123",
  "instruction": "What is the cost of the lab test for glucose?",
  "final_answer": "SELECT cost FROM cost WHERE event_type = 'labevents' AND event_id IN (SELECT row_id FROM labevents WHERE itemid = 50809)",
  "payload": null
}
```

For unanswerable questions:
```json
{
  "task_id": "ehrsql_eicu_valid_456",
  "instruction": "What is the patient's favorite color?",
  "final_answer": "null",
  "payload": null
}
```

## Tips for Success

- **Schema exploration**: Read `schema_notes.py` once per database, then inspect only the relevant tables
- **Value discovery**: Use `find_text_matches.py` before choosing ICD codes, item IDs, lab names, or medication/treatment strings
- **No guessing**: If you have not verified a code, label, or join path in the actual database, do not trust it
- **Testing**: Use `LIMIT 5` when testing queries to avoid huge result sets
- **Dates**: Database timestamps are de-identified (shifted to 2100-2105), so use those dates
- **Batch saves**: Update submission.json every 5-10 tasks to prevent context overflow

## Evaluation

Your submission is evaluated on:
1. **Correctness**: Does your SQL return the right answer?
2. **Answerability**: Did you correctly return "null" for unanswerable questions?
3. **Completion**: Did you answer **every single task**?

Incomplete submissions receive lower scores. **Every task must have a final_answer.**
"""


def _generate_primitive_scripts(workspace_dir: Path) -> None:
    """Generate SQL execution primitive scripts in workspace/scripts/primitives/."""
    scripts_dir = workspace_dir / "scripts" / "primitives"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # schema_notes.py
    (scripts_dir / "schema_notes.py").write_text("""#!/usr/bin/env python3
\"\"\"Print a compact EHRSQL schema cheat sheet for one database.\"\"\"
import argparse
import sys


MIMIC_NOTES = \"\"\"Database: mimic_iii

Identity and joins:
- patients.subject_id identifies a patient
- admissions.hadm_id identifies a hospital admission
- icustays.icustay_id identifies an ICU stay
- Typical path for ICU event questions: patients -> admissions -> icustays -> event table

High-value tables:
- admissions: hospital visit timing, admission/discharge metadata
- icustays: ICU stay timing and IDs
- transfers: care unit movement history; use for careunit questions
- diagnoses_icd + d_icd_diagnoses: diagnosis codes and names
- procedures_icd + d_icd_procedures: procedure codes and names
- labevents + d_labitems: lab results and lab names
- chartevents + d_items: bedside charted events and item labels
- inputevents_cv: ICU intake/medication administration events
- outputevents: ICU output events
- prescriptions: medication orders
- microbiologyevents: specimen descriptions and microbiology tests
- cost: cost rows

Common reminders:
- Do not guess ICD or item codes; derive them from lookup tables
- Questions about "current hospital encounter" often mean admissions.dischtime IS NULL
- Questions about care unit IDs usually belong to transfers, not icustays
\"\"\"


EICU_NOTES = \"\"\"Database: eicu

Identity and joins:
- patient.uniquepid identifies a person across stays
- patient.patientunitstayid identifies a unit stay
- patient.patienthealthsystemstayid identifies a hospitalization across unit stays
- Many questions start from patient.uniquepid, then join to one or more stay rows in patient

High-value tables:
- patient: stay timing, demographics, admission/discharge, weights
- diagnosis: diagnosis names and timing
- medication: ordered/administered drugs
- lab: lab names, values, and timestamps
- intakeoutput: intake/output events, volumes, and timestamps
- treatment: treatment names and timing
- vitalperiodic: repeated vital measurements
- cost: costs
- allergy: allergies and adverse reactions
- microlab: microbiology

Common reminders:
- Search by text values before assuming a diagnosis or medication string
- For hospital-level questions, patienthealthsystemstayid is often the right grouping key
- For current-visit questions, start from the most recent relevant stay for that uniquepid
\"\"\"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-id", required=True, choices=["mimic_iii", "eicu"])
    args = parser.parse_args()

    if args.db_id == "mimic_iii":
        print(MIMIC_NOTES)
        return
    if args.db_id == "eicu":
        print(EICU_NOTES)
        return

    print(f"Unsupported db-id: {args.db_id}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
""")

    # find_text_matches.py
    (scripts_dir / "find_text_matches.py").write_text("""#!/usr/bin/env python3
\"\"\"Search likely text-bearing columns for a case-insensitive keyword.\"\"\"
import argparse
import json
import sqlite3
import sys
from pathlib import Path


TEXT_COLUMNS = {
    "mimic_iii": {
        "d_labitems": ["label", "fluid", "category"],
        "d_items": ["label", "abbreviation", "dbsource", "category", "unitname"],
        "d_icd_diagnoses": ["short_title", "long_title"],
        "d_icd_procedures": ["short_title", "long_title"],
        "prescriptions": ["drug", "drug_name_poe", "drug_name_generic", "formulary_drug_cd", "route"],
        "microbiologyevents": ["spec_type_desc", "org_name", "ab_name", "interpretation"],
        "transfers": ["careunit"],
    },
    "eicu": {
        "diagnosis": ["diagnosisname", "diagnosisstring"],
        "medication": ["drugname", "dosage", "frequency", "drugstopoffset"],
        "treatment": ["treatmentstring"],
        "lab": ["labname"],
        "allergy": ["allergyname", "allergytype", "allergyreaction"],
        "microlab": ["organism", "culturesite", "antibiotic"],
    },
}


def search_column(cursor: sqlite3.Cursor, table: str, column: str, keyword: str, sample_limit: int) -> dict | None:
    query = (
        f"SELECT {column}, COUNT(*) AS n "
        f"FROM {table} "
        f"WHERE {column} IS NOT NULL AND LOWER(CAST({column} AS TEXT)) LIKE ? "
        f"GROUP BY {column} "
        f"ORDER BY n DESC, {column} "
        f"LIMIT ?"
    )
    try:
        rows = cursor.execute(query, (f"%{keyword.lower()}%", sample_limit)).fetchall()
    except sqlite3.Error:
        return None
    if not rows:
        return None
    return {
        "table": table,
        "column": column,
        "matches": [{"value": row[0], "count": row[1]} for row in rows],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-id", required=True, choices=["mimic_iii", "eicu"])
    parser.add_argument("--keyword", required=True, help="Case-insensitive substring to search for")
    parser.add_argument("--sample-limit", type=int, default=8)
    args = parser.parse_args()

    db_file = Path("/data/ehrsql") / args.db_id / f"{args.db_id}.sqlite"
    if not db_file.exists():
        print(f"Error: Database file not found: {db_file}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        results = []
        for table, columns in TEXT_COLUMNS[args.db_id].items():
            for column in columns:
                match = search_column(cursor, table, column, args.keyword, args.sample_limit)
                if match:
                    results.append(match)
        print(json.dumps({
            "db_id": args.db_id,
            "keyword": args.keyword,
            "matches": results,
        }, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
""")

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

    # Pass timeout to sqlite3.connect() instead of setting as attribute
    # (Python 3.12 sqlite3 Connection doesn't allow arbitrary attribute assignment)
    conn = sqlite3.connect(str(db_file), timeout=args.timeout)

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
