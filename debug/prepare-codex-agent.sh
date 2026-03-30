#!/usr/bin/env bash
# Prepare the default Codex agent inside the running Harbor task container.
# This mirrors the auth setup used by src/medcli/agents/harbor/installed/codex.py
# and prints the exact codex exec command to run manually. Codex must already
# be installed; use debug/install-codex-agent.sh first if needed.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
hb::require_running_main

HB_CODEX_AUTH_FILE="$(hb::codex_auth_file)"

: "${HB_CODEX_MODEL:=gpt-5.1-codex-mini}"
: "${HB_CODEX_REASONING_EFFORT:=medium}"
: "${HB_CODEX_INSTRUCTION_PATH:=/tmp/hb-task-instruction.md}"

hb::stage_instruction_in_container "${HB_CODEX_INSTRUCTION_PATH}"

if ! hb::compose exec "${HB_MAIN_SERVICE}" bash -lc '. "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 || true; command -v codex >/dev/null 2>&1'; then
  echo "Codex CLI is not installed in the running container." >&2
  echo "Run: bash debug/install-codex-agent.sh" >&2
  exit 1
fi

hb::compose exec "${HB_MAIN_SERVICE}" bash -lc "
set -euo pipefail
export CODEX_HOME=/logs/agent
mkdir -p /tmp/codex-secrets \"\$CODEX_HOME\"
"
hb::compose cp "${HB_CODEX_AUTH_FILE}" "${HB_MAIN_SERVICE}:/tmp/codex-secrets/auth.json"
hb::compose exec "${HB_MAIN_SERVICE}" bash -lc "
set -euo pipefail
export CODEX_HOME=/logs/agent
ln -sf /tmp/codex-secrets/auth.json \"\$CODEX_HOME/auth.json\"
"

cat <<EOF
Codex agent prepared inside the running container.

In-container environment:
- CODEX_HOME=/logs/agent
- Auth file: /tmp/codex-secrets/auth.json
- Symlink: /logs/agent/auth.json
- Task instruction: ${HB_CODEX_INSTRUCTION_PATH}

Run this inside the container:

export CODEX_HOME=/logs/agent
. ~/.nvm/nvm.sh
codex exec \\
  --dangerously-bypass-approvals-and-sandbox \\
  --skip-git-repo-check \\
  --model ${HB_CODEX_MODEL} \\
  --json \\
  --enable unified_exec \\
  -c model_reasoning_effort=${HB_CODEX_REASONING_EFFORT} \\
  -- "\$(cat ${HB_CODEX_INSTRUCTION_PATH})" \\
  2>&1 </dev/null | stdbuf -oL tee /logs/agent/codex.txt
EOF
