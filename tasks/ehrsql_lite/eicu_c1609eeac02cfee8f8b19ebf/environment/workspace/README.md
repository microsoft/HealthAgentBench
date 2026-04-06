# Workspace Files

- `benchmark_tasks.json`: task definitions for SQL generation
- `submission.json`: editable task rows; fill in `final_answer` (SQL query or "null")

SQLite database:
- eICU: `/data/ehrsql/eicu/eicu.sqlite`

The verifier reads `/workspace/submission.json` after the agent stops.
