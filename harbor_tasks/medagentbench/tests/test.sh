#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /logs/artifacts

: "${VERIFIER_ERROR_ANALYSIS_FILE:=/logs/artifacts/error_analysis.json}"

extra_args=()
if [[ -n "${VERIFIER_ERROR_ANALYSIS_FILE:-}" ]]; then
  extra_args+=(--error-analysis-file "${VERIFIER_ERROR_ANALYSIS_FILE}")
fi

python /tests/verify_meta_task.py           --submission /workspace/submission.json           --tasks /workspace/benchmark_tasks.json           --answer-key /tests/task_answer_key.json           --reward-file /logs/verifier/reward.txt           "${extra_args[@]}"
