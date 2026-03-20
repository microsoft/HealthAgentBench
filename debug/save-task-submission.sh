#!/usr/bin/env bash
# Copy /workspace/submission.json from the running Harbor task container to a
# host-side debug artifact path so later verifier iterations can skip the agent run.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
hb::require_running_main

: "${HB_SUBMISSION_HOST_PATH:=${HOST_ARTIFACTS_PATH}/submission.json}"

mkdir -p "$(dirname "${HB_SUBMISSION_HOST_PATH}")"
hb::compose cp "${HB_MAIN_SERVICE}:/workspace/submission.json" "${HB_SUBMISSION_HOST_PATH}"
echo "${HB_SUBMISSION_HOST_PATH}"
