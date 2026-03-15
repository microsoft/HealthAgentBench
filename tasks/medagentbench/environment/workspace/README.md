# Workspace Files

- `benchmark_tasks.json`: normalized task rows used for task browsing.
- `submission.json`: editable task rows; fill in `final_answer` and `payload`.
- `scripts/primitives/get_*.py`: primitive read helpers; each supports `--help`.
- `scripts/primitives/post_*.py`: simulated write helpers; each supports `--help`.
- `scripts/lib/fhir_common.py`: shared HTTP and payload helpers used by the primitive scripts.

Primitive helper examples:

- `python /workspace/scripts/primitives/get_patient.py --help`
- `python /workspace/scripts/primitives/get_patient.py --identifier S2874099`
- `python /workspace/scripts/primitives/get_observation_labs.py --patient S2823623 --code GLU`
- `python /workspace/scripts/primitives/post_servicerequest.py --help`

The verifier reads `/workspace/submission.json` after the agent stops.
