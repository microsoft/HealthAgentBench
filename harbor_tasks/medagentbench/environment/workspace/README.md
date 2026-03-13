# Workspace Files

- `benchmark_tasks.json`: normalized task rows used for task browsing.
- `submission_template.json`: copy this to `submission.json` and fill in `final_answer` and `payload`.
- `scripts/primitives/fhir_common.py`: shared HTTP and payload helpers used by the primitive scripts.
- `scripts/primitives/get_*.py`: primitive read helpers; each supports `--help`.
- `scripts/primitives/post_*.py`: simulated write helpers; each supports `--help`.
- `scripts/wait_for_fhir.sh`: wait until the local FHIR endpoint is ready.

The verifier reads `/workspace/submission.json` after the agent stops.
