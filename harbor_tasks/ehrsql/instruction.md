# EHRSQL Benchmark - Text-to-SQL Question Answering

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
   - Read the `instruction` field (contains the question + database name like "MIMIC-III" or "eICU")
   - Extract which database to query from the instruction text
   - Use `python scripts/primitives/inspect_schema.py --db-id mimic_iii` (or eicu) to explore tables
   - Cache the schema knowledge to avoid repeating inspections
   - Develop a SQL query to answer the question
   - Test it with `python scripts/primitives/execute_sql.py --db-id mimic_iii --query "SELECT ..."`
   - Write the final SQL query (or the string "null") in `final_answer`
   - Update and save `/workspace/submission.json`
3. **Track progress**: Print "Task X/N completed" periodically so you know how many remain
4. **Complete all tasks**: When you have filled `final_answer` for every single row, confirm you are done

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

- **Schema exploration**: Load each database's schema once, then reuse that knowledge
- **Pattern recognition**: Find common SQL patterns (e.g., joining to lookup tables) and adapt them
- **Testing**: Use `LIMIT 5` when testing queries to avoid huge result sets
- **Dates**: Database timestamps are de-identified (shifted to 2100-2105), so use those dates
- **Batch saves**: Update submission.json every 5-10 tasks to prevent context overflow

## Evaluation

Your submission is evaluated on:
1. **Correctness**: Does your SQL return the right answer?
2. **Answerability**: Did you correctly return "null" for unanswerable questions?
3. **Completion**: Did you answer **every single task**?

Incomplete submissions receive lower scores. **Every task must have a final_answer.**
