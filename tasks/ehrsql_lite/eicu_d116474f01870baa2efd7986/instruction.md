# EHRSQL: Text-to-SQL over EHR Data

You are working inside a task environment that contains:

- a eICU SQLite EHR database at `/data/ehrsql/eicu/eicu.sqlite`
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

- eICU: `/data/ehrsql/eicu/eicu.sqlite`
