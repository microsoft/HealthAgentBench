#!/bin/bash
# gpt-6.1-sol is only deployed on Azure OpenAI East US. Route Harbor's built-in Codex agent there.
# - CODEX_FORCE_AUTH_JSON must be exported as a false value in the SHELL (not unset: Harbor's import-time
#   load_dotenv() re-reads .env and would restore =1; not via the yaml env block: agent env values are
#   redacted from every copied trial file, and a value like "0" corrupts result.json).
# - The Azure v1 endpoint accepts the key as a Bearer token, so OPENAI_API_KEY/OPENAI_BASE_URL suffice.
cd /home/qianchuliu/projects/HealthAgentBench || exit 1
set -a; source .env; set +a
export CODEX_FORCE_AUTH_JSON=false
export OPENAI_API_KEY="$AZURE_OPENAI_EUS_API_KEY"
export OPENAI_BASE_URL=https://hanoveroaieus.openai.azure.com/openai/v1
Y=${1:-full_run_v2/healthagentbench_nonimaging_gpt-6.1-sol_azure.yaml}
mkdir -p full_run_v2/codex_gpt-6.1-sol_azure
setsid nohup uv run harbor run -c "$Y" -y > full_run_v2/codex_gpt-6.1-sol_azure/launch.log 2>&1 < /dev/null &
sleep 2; pgrep -af "harbor run -c $Y" | grep -v pgrep | head -1 | cut -c1-120
