# MedAgentBench Debug

This directory contains MedAgentBench-specific debug helpers built on top of the generic Harbor debug workflow in `debug/README.md`.

## Helpers

Use `debug/README.md` for the shared environment lifecycle and verifier flow, then use the wrappers here for benchmark-specific tasks such as:

- `check-workspace.sh`
- `init-perfect-submission.py`
- `smoke-meta-task.sh`
- `run-manually.sh`

These helpers assume the generated task lives at `tasks/medagentbench/`.

## What Each Helper Does

1. `check-workspace.sh`
- Runs basic in-container checks:
  - lists `/workspace`
  - exercises the helper scripts
  - inspects the prepared `submission.json`

2. `init-perfect-submission.py`
- Builds a synthetic perfect submission payload based on the selected benchmark slice and hidden answer key.
- By default it prints JSON to stdout; the smoke wrapper writes it to a temp file and copies it into the live task container.

3. `smoke-meta-task.sh`
- Runs the full non-agent smoke path:
  1. build task environment
  2. start environment
  3. check workspace
  4. generate a perfect submission and copy it into the live container
  5. run verifier directly

4. `run-manually.sh`
- Recommended one-command manual Codex workflow for MedAgentBench.
- Requires `CODEX_AUTH_JSON` in the host shell.
- Calls the generic `debug/setup-agent.sh`, then opens a shell where `codex` is already available.

## Recommended Wrapper Flow

Use the generic environment build/start steps, then hand off to the one-command benchmark wrapper:

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
bash debug/build-task-env.sh
bash debug/up-task-env.sh
bash debug/medagentbench/run-manually.sh
```

For the smoke path:

```bash
bash debug/medagentbench/smoke-meta-task.sh
```

For the current MedAgentBench task, verifier-only debugging also writes:

- `.tmp/<project>/verifier/error_analysis.json`

That file merges the submission rows with the hidden answer-key fields by `task_id`.
