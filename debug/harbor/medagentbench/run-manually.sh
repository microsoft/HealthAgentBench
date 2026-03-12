#!/usr/bin/env bash
# Prepare a ready-to-use manual MedAgentBench Codex session, then open a shell
# in the running Harbor task container.
set -euo pipefail
source "$(dirname "$0")/../common.sh"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

export HB_TASK_DIR="${HB_TASK_DIR:-harbor_tasks/medagentbench}"
export HB_PROJECT_NAME="${HB_PROJECT_NAME:-medagentbench-debug}"
export HB_READY_CODEX_SHELL=1

hb::setup_task_env
hb::require_running_main
hb::require_var CODEX_AUTH_JSON

cat <<EOF
Recommended MedAgentBench manual workflow

This command will now:
- install Codex in the running container if needed
- stage the task instruction at /tmp/hb-task-instruction.md
- prepare /logs/agent/auth.json and CODEX_HOME=/logs/agent
- open a shell where codex is already available

Inside the opened container shell:

1. Initialize and inspect the task:
   /workspace/scripts/wait_for_fhir.sh
   python /workspace/scripts/init_submission.py
   sed -n '1,200p' /workspace/benchmark_tasks.json
   sed -n '1,160p' /workspace/submission.json

2. Use the helper scripts while editing /workspace/submission.json:
   python /workspace/scripts/fhir_tools.py patient-age --mrn S2874099
   python /workspace/scripts/fhir_tools.py latest-observation --patient S2823623 --code GLU
   python /workspace/scripts/show_action_template.py task8_1

3. Run the default Codex agent command inside the container:
   export CODEX_HOME=/logs/agent
   codex exec \\
     --dangerously-bypass-approvals-and-sandbox \\
     --skip-git-repo-check \\
     --model gpt-5.1-codex-mini \\
     --json \\
     --enable unified_exec \\
     -c model_reasoning_effort=medium \\
     -- "\$(cat /tmp/hb-task-instruction.md)" \\
     2>&1 </dev/null | stdbuf -oL tee /logs/agent/codex.txt

4. After the agent run finishes, exit the shell and run:
   bash debug/harbor/run-task-verifier.sh
EOF

printf '\nInstalling Codex if needed and preparing the container.\n\n'
bash "${ROOT_DIR}/debug/harbor/setup-agent.sh"

printf '\nHanding off to the generic manual task runner.\n\n'
bash "${ROOT_DIR}/debug/harbor/run-task-manually.sh"
