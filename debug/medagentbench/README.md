# MedAgentBench Debug

This directory contains MedAgentBench-specific debug helpers built on top of the generic Harbor debug workflow in `debug/README.md`.

Use `debug/README.md` for the shared environment lifecycle and verifier flow, then use the wrappers here for benchmark-specific tasks such as:

- `check-workspace.sh`
- `init-perfect-submission.py`
- `smoke-meta-task.sh`
- `run-manually.sh`

These helpers assume the generated task lives at `tasks/medagentbench/`.
