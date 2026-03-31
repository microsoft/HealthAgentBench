#!/bin/bash
# Run Harbor job for MedAgentBench.
# Automatically downloads data and generates tasks if needed.
# Harbor's built-in verifier handles per-task evaluation automatically.
#
# Usage:
#   bash scripts/medagentbench/run_and_evaluate.sh jobs/medagentbench_meta.yaml
#   bash scripts/medagentbench/run_and_evaluate.sh jobs/medagentbench_meta.yaml -m gpt-5.1-codex-mini --ak reasoning_effort=low

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$SCRIPT_DIR/assets"
TASK_DIR="tasks/medagentbench"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <job-yaml> [harbor run flags...]"
    exit 1
fi

JOB_YAML="$1"
shift

# --- Step 1: Download data if needed ---
if [ ! -f "$ASSETS_DIR/test_data_v2.json" ]; then
    echo "=== Downloading MedAgentBench data ==="
    bash "$SCRIPT_DIR/setup.sh"
fi

# --- Step 2: Generate tasks if needed ---
if [ ! -d "$TASK_DIR" ] || [ ! -f "$TASK_DIR/task.toml" ]; then
    echo "=== Generating tasks at $TASK_DIR ==="
    uv run python scripts/medagentbench/generate_harbor_tasks.py \
        --input-json "$ASSETS_DIR/test_data_v2.json" \
        --output-root "$TASK_DIR"
fi

# --- Step 3: Run Harbor ---
echo "=== Running Harbor job: $JOB_YAML $* ==="
uv run harbor run -c "$JOB_YAML" "$@"
