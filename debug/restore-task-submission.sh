#!/usr/bin/env bash
# Copy a host-side submission snapshot back into the running Harbor task
# container so verifier/debug steps can be rerun without another agent pass.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
hb::require_running_main

: "${HB_SUBMISSION_HOST_PATH:=${HOST_ARTIFACTS_PATH}/submission.json}"

if [[ ! -f "${HB_SUBMISSION_HOST_PATH}" ]]; then
  echo "missing saved submission: ${HB_SUBMISSION_HOST_PATH}" >&2
  exit 1
fi

hb::compose cp "${HB_SUBMISSION_HOST_PATH}" "${HB_MAIN_SERVICE}:/workspace/submission.json"
echo "${HB_SUBMISSION_HOST_PATH}"
