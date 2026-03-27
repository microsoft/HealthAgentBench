# EHRSQL: Text-to-SQL over EHR Data

## Environment
You have access to two SQLite databases mounted at `/data/ehrsql/`:
- MIMIC-III: `/data/ehrsql/mimic_iii/mimic_iii.sqlite`
- eICU: `/data/ehrsql/eicu/eicu.sqlite
The task data is provided in `/workspace/benchmark_tasks.json`, and you should write your answers to `/workspace/submission.json`.

## Helper Scripts

Use these scripts to manage tasks:

```bash
# Get a task by row index (0-indexed)
./scripts/primitives/get_row.py 0

# Update answer for a task
./scripts/primitives/set_answer.py 0 "SELECT * FROM patients WHERE ..."
```

## Workflow

**You must complete ALL rows in a single continuous run. Do not stop until every row is answered.**

Use a tight loop to systematically work through every row:

```python
# Pseudocode for your workflow:
for row_index in range(0, total_rows):
    get_row(row_index)
    generate SQL answer (or "null" if unanswerable)
    set_answer(row_index, sql)
    # Continue immediately to next row—do not pause
```

For each row from `benchmark_tasks.json`:

1. Run: `python ./scripts/primitives/get_row.py ROW_INDEX`
2. Read the `instruction` field (natural language question)
3. Generate a SQL query that answers it (or "null" if unanswerable)
4. Run: `python ./scripts/primitives/set_answer.py ROW_INDEX "YOUR_SQL_QUERY"`
5. **Immediately proceed to the next row** — do not stop or wait for user input

**This is a single, continuous task.** You will receive no further input once you start. Work through rows 0 → N (where N is the last row) without interruption.

## Example: Continuous Execution

Row 0:
```bash
python ./scripts/primitives/get_row.py 0
python ./scripts/primitives/set_answer.py 0 "SELECT COUNT(*) FROM patients"
# ✓ Row 0 updated | Progress: 1/200 (0.5%)
```

Row 1 (immediately—no pause):
```bash
python ./scripts/primitives/get_row.py 1
python ./scripts/primitives/set_answer.py 1 "SELECT dob FROM patients WHERE subject_id = 45601"
# ✓ Row 1 updated | Progress: 2/200 (1.0%)
```

**Continue this loop through all rows without stopping or asking for input.**

## Databases

- MIMIC-III: `/data/ehrsql/mimic_iii/mimic_iii.sqlite`
- eICU: `/data/ehrsql/eicu/eicu.sqlite`

## IMPORTANT: Benchmark Integrity

**Do not look up answers online or in external sources.** This includes:
- ❌ Downloading EHRSQL datasets from GitHub or other repositories
- ❌ Searching for task instructions online to find expected answers
- ❌ Using any pre-computed answer files or databases
- ❌ Copying SQL from external EHRSQL implementations

**You must generate SQL based on:**
- ✓ Database schema inspection (using SQLite PRAGMA commands)
- ✓ Experimentation with the mounted databases
- ✓ Your understanding of the question and data

Violating this will invalidate your submission and compromise the benchmark.

## Evaluation

Your submission is evaluated on:
1. **Correctness**: Does your SQL return the right answer?
2. **Answerability**: Did you correctly return "null" for truly unanswerable tasks?
3. **Completion**: Did you answer **every single task**?

**Your final work product is `/workspace/submission.json`.**
