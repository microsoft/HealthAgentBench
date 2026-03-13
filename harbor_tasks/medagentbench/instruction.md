# EHR Workflow Benchmark

You are working inside a task environment that contains:

- a local FHIR server at `http://fhir:8080/fhir`
- task descriptions at `/workspace/benchmark_tasks.json`
- editable task rows already prepared at `/workspace/submission.json`
- primitive FHIR helper scripts under `/workspace/scripts/primitives/` (each supports `--help`)

Primitive helper examples:
- `python /workspace/scripts/primitives/get_patient.py --help`
- `python /workspace/scripts/primitives/get_patient.py --identifier S2874099`
- `python /workspace/scripts/primitives/get_observation_labs.py --patient S2823623 --code GLU`
- `python /workspace/scripts/primitives/post_servicerequest.py --help`

This benchmark simulates realistic EHR workflows in which each task may require multiple retrieval and action steps over patient data.
The environment provides API-style helper scripts for interacting with the EHR. Work through the tasks carefully and complete each row accurately.

Your final work product is `/workspace/submission.json`.

Suggested workflow:

1. Choose one row from `/workspace/submission.json`.
2. Read that row's instruction carefully.
3. Use the helper scripts under `/workspace/scripts/primitives/` when you need to query the chart or simulate a write. Start with `--help` if you are unsure which primitive to use.
4. Write the row's `final_answer` and `payload`, then move to the next row.
5. Stop when every row is complete.

Submission rules:

- `/workspace/submission.json` is a JSON list. Each row contains `task_id`, task text, and exactly two editable result fields: `final_answer` and `payload`.
- For query-only tasks, set `final_answer` and leave `payload` as `null`.
- For write tasks, use the simulated POST helpers. They do not mutate the database; instead they print an accepted payload for you to copy into `payload`.
- If a task needs multiple writes, set `payload` to a list of payload objects in call order. Otherwise use one payload object or `null`.
- Do not add new fields to the submission rows.
