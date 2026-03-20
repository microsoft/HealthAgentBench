#!/usr/bin/env bash
# Present the current Harbor task context, stage the task instruction into the
# live container, and then hand off to an interactive shell for manual work.
# When HB_READY_CODEX_SHELL=1, open a shell with CODEX_HOME and NVM/Codex
# already loaded so the agent can be run immediately.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
hb::require_running_main

: "${HB_CODEX_INSTRUCTION_PATH:=/tmp/hb-task-instruction.md}"

instruction_path="$(hb::instruction_path)"
hb::stage_instruction_in_container "${HB_CODEX_INSTRUCTION_PATH}"

cat <<EOF
Manual Harbor task run context

Task directory: ${HB_TASK_DIR_ABS}
Instruction file: ${instruction_path}
Instruction staged in container at: ${HB_CODEX_INSTRUCTION_PATH}
Main container service: ${HB_MAIN_SERVICE}
Container workspace: /workspace
Container agent logs: /logs/agent
Container verifier logs: /logs/verifier
Host agent logs: ${HOST_AGENT_LOGS_PATH}
Host verifier logs: ${HOST_VERIFIER_LOGS_PATH}

Task instruction:
EOF
printf '\n'
sed -n '1,260p' "${instruction_path}"
printf '\n'

cat <<EOF
To prepare the default Codex agent setup from another terminal:
  bash debug/prepare-codex-agent.sh

Dropping into the running task container now.
EOF

if [[ "${HB_READY_CODEX_SHELL:-0}" == "1" ]]; then
  hb::compose exec "${HB_MAIN_SERVICE}" bash -lc '
set -euo pipefail
export CODEX_HOME=/logs/agent
. "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 || true
exec bash -i
'
else
  hb::compose exec "${HB_MAIN_SERVICE}" bash
fi
