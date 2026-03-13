# Workspace Files

- `benchmark_tasks.json`: normalized MedAgentBench task rows used for task browsing.
- `submission_template.json`: copy this to `submission.json` and fill in `final_answer` and `payload`.
- `action_payload_templates.json`: reference payloads for the selected write tasks.
- `scripts/fhir_primitives.py`: primitive GET and simulated POST helpers.
- `scripts/show_action_template.py <task_id>`: print the reference payload for a selected task.
- `scripts/wait_for_fhir.sh`: wait until the local FHIR endpoint is ready.

The verifier reads `/workspace/submission.json` after the agent stops.
