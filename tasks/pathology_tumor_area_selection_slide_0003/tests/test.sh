#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier /logs/artifacts

python /tests/verify_meta_task.py   --submission /workspace/submission.json   --answer-key /tests/task_answer_key.json   --reward-txt /logs/verifier/reward.txt   --results-json /logs/verifier/meta_results.json   --error-analysis-file /logs/verifier/error_analysis.json
