#!/bin/bash
# Re-run the six compositional-QA tasks with the shared 1020-row train set (ChatGPT auth route), 5 concurrent per model.
cd /home/qianchuliu/projects/HealthAgentBench || exit 1
set -a; source .env; set +a
for m in gpt-5.6-sol gpt-6-sol gpt-6-astra; do
  mkdir -p full_run_v2/cqa_sharedtrain_codex_$m
  setsid nohup uv run harbor run -c full_run_v2/cqa_sharedtrain_$m.yaml -y > full_run_v2/cqa_sharedtrain_codex_$m/launch.log 2>&1 < /dev/null &
done
sleep 3; pgrep -af "cqa_sharedtrain_" | grep -v pgrep | cut -c1-120
