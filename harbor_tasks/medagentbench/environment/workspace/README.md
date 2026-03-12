# Workspace Files

- `benchmark_tasks.json`: the 10 selected MedAgentBench items to solve.
- `submission_template.json`: copy this to `submission.json` and fill it in.
- `action_payload_templates.json`: example payload shapes for the action-scored tasks.
- `scripts/fhir_tools.py`: helper CLI for common FHIR queries.
- `scripts/show_action_template.py <task_id>`: print the template payload for an action task.
- `scripts/wait_for_fhir.sh`: wait until the local FHIR endpoint is ready.

The verifier reads `/workspace/submission.json` after the agent stops.
