#!/bin/bash
set -euo pipefail

SUBMISSION="${SUBMISSION_PATH:-/workspace/submission.json}"
ANSWER_KEY="${ANSWER_KEY_PATH:-/tests/answer_key.json}"
METRICS_OUT="${HARBOR_METRICS_PATH:-/logs/verifier/metrics.json}"
REWARD_OUT="${HARBOR_REWARD_PATH:-/logs/verifier/reward.json}"

mkdir -p "$(dirname "$METRICS_OUT")" "$(dirname "$REWARD_OUT")"

python3 /tests/evaluator.py \
    --submission "$SUBMISSION" \
    --answer-key "$ANSWER_KEY" \
    --metrics-out "$METRICS_OUT" \
    --reward-out "$REWARD_OUT"
