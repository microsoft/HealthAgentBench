#!/usr/bin/env bash
# Run the MedAgentBench Harbor meta-task debug flow without a real agent.
# This builds the environment, starts the stack, performs workspace checks,
# injects a perfect submission into the live container, and runs the verifier.
set -euo pipefail
source "$(dirname "$0")/../common.sh"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

export HB_TASK_DIR="${HB_TASK_DIR:-tasks/medagentbench}"
export HB_PROJECT_NAME="${HB_PROJECT_NAME:-medagentbench-debug}"

"${ROOT_DIR}/debug/build-task-env.sh"
"${ROOT_DIR}/debug/up-task-env.sh"
"${ROOT_DIR}/debug/medagentbench/check-workspace.sh"
hb::setup_task_env
perfect_submission_path="${ROOT_DIR}/.tmp/medagentbench-hb/perfect-submission.json"
python "${ROOT_DIR}/debug/medagentbench/init-perfect-submission.py" \
  --task-dir "${ROOT_DIR}/${HB_TASK_DIR}" \
  --output "${perfect_submission_path}"
hb::compose cp "${perfect_submission_path}" "${HB_MAIN_SERVICE}:/workspace/submission.json"
"${ROOT_DIR}/debug/run-task-verifier.sh"

echo "cleanup with: ${ROOT_DIR}/debug/down-task-env.sh"
