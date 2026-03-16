# EHRSQL Benchmark - Text-to-SQL Question Answering

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
  "instruction": "What is the method of intake for clobetasol propionate 0.05% ointment?\n\nDatabase: MIMIC-III",
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
