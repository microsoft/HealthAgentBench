# EHRSQL Workspace

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
python scripts/primitives/execute_sql.py \
  --db-id mimic_iii \
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
