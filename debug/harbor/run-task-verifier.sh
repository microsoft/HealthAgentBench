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

hb::compose exec "${HB_MAIN_SERVICE}" bash -lc 'rm -rf /tests && mkdir -p /tests'
hb::compose cp "${HB_TASK_DIR_ABS}/tests/." "${HB_MAIN_SERVICE}:/tests"
hb::compose exec "${HB_MAIN_SERVICE}" bash -lc 'chmod +x /tests/test.sh && /tests/test.sh > /logs/verifier/test-stdout.txt 2>&1'

cat "${HOST_VERIFIER_LOGS_PATH}/reward.txt"
