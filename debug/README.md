# Debug Helpers

This directory contains reusable debugging helpers for Harbor task environments, plus thin benchmark-specific wrappers.

## Layout

- `debug/harbor/` — reusable Harbor task debugging scripts.
- `debug/harbor/medagentbench/` — MedAgentBench-specific helpers built on top of the Harbor layer.

## Harbor Helpers

All scripts default to the generated MedAgentBench Harbor task at `harbor_tasks/medagentbench`, but they can be reused for other Harbor tasks by setting environment variables before running them.

Common environment variables:

- `HB_TASK_DIR`: Harbor task directory relative to repo root.
  - Default: `harbor_tasks/medagentbench`
- `HB_PROJECT_NAME`: Docker Compose project name for the debug stack.
  - Default: `medagentbench-debug`
- `HB_MAIN_IMAGE_NAME`: main task image name.
  - Default: `hb__$(basename "$HB_TASK_DIR")`
- `HB_MAIN_SERVICE`: service name to open a shell into.
  - Default: `main`
- `HB_CPUS`: CPU limit for the debug stack.
  - Default: task `task.toml` `[environment].cpus`
- `HB_MEMORY`: memory limit for the debug stack.
  - Default: task `task.toml` `[environment].memory_mb`

Reusable Harbor scripts:

1. `debug/harbor/build-task-env.sh`
- Builds the Harbor task environment image using Harbor's Docker Compose base/build files plus the task's own `environment/docker-compose.yaml`.

2. `debug/harbor/up-task-env.sh`
- Starts the Harbor task environment and waits for the containers to become healthy.
- This mirrors Harbor's startup pattern by doing `down --remove-orphans` before `up -d --wait`.
- For the MedAgentBench task, `main` is gated on a separate readiness helper service that waits for the pinned FHIR sidecar to answer `/fhir/metadata`.

3. `debug/harbor/exec-task-shell.sh`
- Opens an interactive shell inside the task `main` container.

4. `debug/harbor/run-task-manually.sh`
- Prints the current task instruction and runtime paths, stages the task instruction into the live container at `/tmp/hb-task-instruction.md`, and opens an interactive shell in `main`.
- When `HB_READY_CODEX_SHELL=1`, it opens a shell with `CODEX_HOME=/logs/agent` and the NVM/Codex environment preloaded.

5. `debug/harbor/prepare-codex-agent.sh`
- Prepares the default Codex agent setup inside the live container using the same auth and `CODEX_HOME` layout as `src/medcli/agents/harbor/installed/codex.py`.
- Requires the Codex CLI to already be installed inside the running container.
- Prints the exact `codex exec` command to run manually inside the container.

6. `debug/harbor/install-codex-agent.sh`
- Installs the Codex CLI inside the running container using the same steps as Harbor's `install-codex.sh.j2` template.
- If Codex is already installed, it prints the existing version and exits.

7. `debug/harbor/setup-agent.sh`
- Sets up the default Harbor debug agent after `up-task-env.sh`.
- For now, the default agent is Codex, so this helper runs:
  - `install-codex-agent.sh`
  - `prepare-codex-agent.sh`

8. `debug/harbor/run-task-verifier.sh`
- Runs the task verifier the same way Harbor does:
  - copies the task `tests/` directory into the running container at `/tests`
  - executes `/tests/test.sh`
  - reads the mounted verifier outputs from `.tmp/<project>/verifier/`
- This means the task environment must already be running.

9. `debug/harbor/show-task-logs.sh`
- Prints the latest Harbor run/trial files, trial log, agent log, verifier stdout, and reward.
- Optional arg: explicit Harbor run directory.

10. `debug/harbor/down-task-env.sh`
- Stops and removes the debug Docker Compose stack.
- Set `HB_FULL_CLEANUP=1` to mirror Harbor's heavier cleanup path and also remove images and volumes.

## MedAgentBench Helpers

These scripts assume the current single-task MedAgentBench Harbor meta-task.

1. `debug/harbor/medagentbench/check-workspace.sh`
- Runs basic in-container checks:
  - lists `/workspace`
  - waits for the FHIR sidecar
  - exercises the helper scripts
  - initializes `submission.json`

2. `debug/harbor/medagentbench/init-perfect-submission.py`
- Builds a synthetic perfect submission payload based on the selected benchmark slice and action payload templates.
- By default it prints JSON to stdout; the smoke wrapper writes it to a temp file and copies it into the live task container.

3. `debug/harbor/medagentbench/smoke-meta-task.sh`
- Runs the full non-agent smoke path:
  1. build task environment
  2. start environment
  3. check workspace
  4. generate a perfect submission and copy it into the live container
  5. run verifier directly

4. `debug/harbor/medagentbench/run-manually.sh`
- Recommended one-command manual Codex workflow for MedAgentBench.
- Requires `CODEX_AUTH_JSON` in the host shell.
- Calls the generic `debug/harbor/setup-agent.sh`, then opens a shell where `codex` is already available.

## Recommended Workflows

### 1. Fast verifier smoke test

```bash
bash debug/harbor/medagentbench/smoke-meta-task.sh
```

Expected outcome:
- environment builds and starts
- pinned FHIR sidecar responds
- helper scripts work
- verifier returns `1.000000`

### 2. Manual environment debugging

```bash
bash debug/harbor/build-task-env.sh
bash debug/harbor/up-task-env.sh
bash debug/harbor/exec-task-shell.sh
```

Inside the container, you can inspect `/workspace` and run the helper scripts manually.

When finished:

```bash
bash debug/harbor/down-task-env.sh
```

### 3. Manual task execution with Codex

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
bash debug/harbor/build-task-env.sh
bash debug/harbor/up-task-env.sh
bash debug/harbor/setup-agent.sh
bash debug/harbor/run-task-manually.sh
```

Or, for the current MedAgentBench task, use the one-command wrapper:

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
bash debug/harbor/build-task-env.sh
bash debug/harbor/up-task-env.sh
bash debug/harbor/medagentbench/run-manually.sh
```

Inside the opened container shell:

```bash
python /workspace/scripts/init_submission.py
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  --model gpt-5.1-codex-mini \
  --json \
  --enable unified_exec \
  -c model_reasoning_effort=medium \
  -- "$(cat /tmp/hb-task-instruction.md)" \
  2>&1 </dev/null | stdbuf -oL tee /logs/agent/codex.txt
```

When the agent finishes, exit the shell and run:

```bash
bash debug/harbor/run-task-verifier.sh
```

### 4. Verifier-only debugging

Create or edit a submission file, then run:

```bash
bash debug/harbor/run-task-verifier.sh
```

This prints the reward and writes verifier artifacts under `.tmp/<project>/verifier/`.

### 5. Harbor trial log inspection

After running Harbor normally:

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
UV_CACHE_DIR=.uv-cache uv run harbor run -c jobs/medagentbench_meta.yaml
bash debug/harbor/show-task-logs.sh
```

## Notes

- The reusable Harbor scripts intentionally do not hard-code MedAgentBench-specific verifier logic.
- The MedAgentBench wrapper scripts are thin orchestration helpers on top of the generic Harbor layer.
- The debug stack uses Harbor's default `hb__<task-name>` image naming for the main task image.
- `up-task-env.sh` intentionally runs `docker compose down --remove-orphans` before `up -d --wait` to match Harbor's `DockerEnvironment.start()` behavior.
- The generated Harbor task tree should stay source-only. If you see `harbor_tasks/medagentbench/environment/workspace/submission.json` on disk after debugging, remove it; the canonical runtime copy belongs inside the running container or under `.tmp/`.
- `install-codex-agent.sh` mirrors Harbor's `install-codex.sh.j2` behavior closely: it installs NVM, Node 22, and `@openai/codex`, then prints the installed Codex version.
- `prepare-codex-agent.sh` expects `CODEX_AUTH_JSON` in the host shell and writes the auth file into the live container using the same `/tmp/codex-secrets` and `/logs/agent/auth.json` layout as the Harbor-installed Codex wrapper.
- `setup-agent.sh` is the default generic post-`up-task-env.sh` step when Codex is the debug agent; task-specific wrappers can call it instead of duplicating install/setup commands.
