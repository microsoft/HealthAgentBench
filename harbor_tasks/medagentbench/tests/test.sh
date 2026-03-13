#!/usr/bin/env bash
set -euo pipefail

python /tests/verify_meta_task.py           --submission /workspace/submission.json           --tasks /workspace/benchmark_tasks.json           --answer-key /tests/task_answer_key.json           --reward-file /logs/verifier/reward.txt
