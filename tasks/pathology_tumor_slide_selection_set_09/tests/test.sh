#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier /logs/artifacts

python /tests/verify.py \
  --submission /workspace/submission.json \
  --answer-key /tests/task_answer_key.json \
  --reward-txt /logs/verifier/reward.txt \
  --metrics-json /logs/verifier/metrics.json \
  --error-analysis-file /logs/verifier/error_analysis.json
