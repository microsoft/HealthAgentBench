#!/usr/bin/env bash
# Show the latest Harbor run and trial logs for a task, including verifier
# stdout/reward files when they exist.
set -euo pipefail
source "$(dirname "$0")/common.sh"

RUN_DIR="${1:-$(hb::latest_harbor_run)}"
if [[ -z "${RUN_DIR}" ]]; then
  echo "no Harbor run directory found" >&2
  exit 1
fi
TRIAL_DIR="$(hb::latest_trial_dir "${RUN_DIR}")"

echo "run_dir=${RUN_DIR}"
echo "--- run files ---"
find "${RUN_DIR}" -maxdepth 1 -type f | sort
echo "--- config.json ---"
sed -n '1,200p' "${RUN_DIR}/config.json" 2>/dev/null || true
echo "--- job.log ---"
sed -n '1,200p' "${RUN_DIR}/job.log" 2>/dev/null || true
echo "--- result.json ---"
sed -n '1,200p' "${RUN_DIR}/result.json" 2>/dev/null || true

if [[ -z "${TRIAL_DIR}" ]]; then
  echo "no trial directory found under ${RUN_DIR}" >&2
  exit 0
fi

echo "trial_dir=${TRIAL_DIR}"
find "${TRIAL_DIR}" -maxdepth 3 -type f | sort

echo "--- trial.log ---"
sed -n '1,200p' "${TRIAL_DIR}/trial.log" 2>/dev/null || true

echo "--- agent files ---"
find "${TRIAL_DIR}/agent" -maxdepth 2 -type f | sort 2>/dev/null || true
echo "--- agent/codex.txt ---"
sed -n '1,240p' "${TRIAL_DIR}/agent/codex.txt" 2>/dev/null || true

echo "--- verifier/test-stdout.txt ---"
sed -n '1,240p' "${TRIAL_DIR}/verifier/test-stdout.txt" 2>/dev/null || true

echo "--- verifier/reward.txt ---"
cat "${TRIAL_DIR}/verifier/reward.txt" 2>/dev/null || true
