# Workspace Files

- `benchmark_tasks.json`: normalized MedAgentBench task rows used for task browsing.
- `submission_template.json`: copy this to `submission.json` and fill in `final_answer` and `payload`.
- `scripts/fhir_primitives.py`: primitive GET and simulated POST helpers.
- `scripts/wait_for_fhir.sh`: wait until the local FHIR endpoint is ready.

The verifier reads `/workspace/submission.json` after the agent stops.
