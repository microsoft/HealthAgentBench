#!/usr/bin/env bash
# Run a Harbor task verifier the same way Harbor does.
# This uploads the task's tests/ directory into the live container, executes
# /tests/test.sh there, and then reads reward/log outputs from the mounted
# verifier log directory under .tmp/.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
rm -rf "${HOST_VERIFIER_LOGS_PATH:?}/"*
mkdir -p "${HOST_VERIFIER_LOGS_PATH}"
: "${HB_ERROR_ANALYSIS_FILE:=/logs/verifier/error_analysis.json}"

hb::compose exec "${HB_MAIN_SERVICE}" bash -lc 'rm -rf /tests && mkdir -p /tests /logs/verifier'
hb::compose cp "${HB_TASK_DIR_ABS}/tests/." "${HB_MAIN_SERVICE}:/tests"
hb::compose exec \
  -e VERIFIER_ERROR_ANALYSIS_FILE="${HB_ERROR_ANALYSIS_FILE}" \
  "${HB_MAIN_SERVICE}" \
  bash -lc 'mkdir -p /logs/verifier && chmod +x /tests/test.sh && /tests/test.sh' \
  > "${HOST_VERIFIER_LOGS_PATH}/test-stdout.txt" 2>&1

cat "${HOST_VERIFIER_LOGS_PATH}/reward.txt"
