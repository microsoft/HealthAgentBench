# Workspace Files

- `benchmark_tasks.json`: task definitions for SQL generation
- `submission.json`: editable task rows; fill in `final_answer` (SQL query or "null")

SQLite database:
- MIMIC-III: `/data/ehrsql/mimic_iii/mimic_iii.sqlite`

The verifier reads `/workspace/submission.json` after the agent stops.
