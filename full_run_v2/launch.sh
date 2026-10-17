#!/bin/bash
# Launch the v2 full-benchmark sweep: gpt-6-astra (ChatGPT login) and gpt-6.1-sol (Azure East US), 5 concurrent each.
cd /home/qianchuliu/projects/HealthAgentBench || exit 1
set -a; source .env; set +a
mkdir -p full_run_v2/codex_gpt-6-astra full_run_v2/codex_gpt-6.1-sol
# astra: ChatGPT auth.json route (CODEX_FORCE_AUTH_JSON from .env)
setsid nohup uv run harbor run -c full_run_v2/healthagentbench_full_gpt-6-astra.yaml -y \
  > full_run_v2/codex_gpt-6-astra/launch.log 2>&1 < /dev/null &
# gpt-6.1-sol: Azure OpenAI East US via API key (Bearer accepted by the v1 endpoint)
( unset CODEX_FORCE_AUTH_JSON; export OPENAI_API_KEY="$AZURE_OPENAI_EUS_API_KEY" OPENAI_BASE_URL=https://hanoveroaieus.openai.azure.com/openai/v1
  setsid nohup uv run harbor run -c full_run_v2/healthagentbench_full_gpt-6.1-sol_azure.yaml -y \
    > full_run_v2/codex_gpt-6.1-sol/launch.log 2>&1 < /dev/null & )
sleep 2; pgrep -af "full_run_v2/healthagentbench_full" | grep -v pgrep | cut -c1-120
