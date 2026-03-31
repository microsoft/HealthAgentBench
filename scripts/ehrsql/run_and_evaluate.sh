#!/bin/bash
# Run Harbor job and automatically aggregate results afterward.
# Automatically downloads data and generates tasks if needed.
#
# Usage:
#   bash scripts/ehrsql/run_and_evaluate.sh jobs/ehrsql_eicu_test_meta.yaml
#   bash scripts/ehrsql/run_and_evaluate.sh jobs/ehrsql_eicu_test_meta.yaml -m gpt-5.1-codex-mini --ak reasoning_effort=low

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_SIZE=250
SPLIT_N=250

if [ $# -lt 1 ]; then
    echo "Usage: $0 <job-yaml> [harbor run flags...]"
    exit 1
fi

JOB_YAML="$1"
shift

# Extract jobs_dir and task path from yaml
JOBS_DIR=$(grep '^jobs_dir:' "$JOB_YAML" | awk '{print $2}')
TASK_DIR=$(grep '^\s*- path:' "$JOB_YAML" | head -1 | awk '{print $3}')
# e.g. tasks/ehrsql/mimic_iii_test -> db=mimic_iii, split=test
TASK_BASENAME=$(basename "$TASK_DIR")                    # mimic_iii_test
DB_ID="${TASK_BASENAME%_*}"                              # mimic_iii
SPLIT="${TASK_BASENAME##*_}"                             # test

# Map split to JSON arg name
if [ "$SPLIT" = "valid" ]; then
    JSON_FLAG="--valid-json"
else
    JSON_FLAG="--test-json"
fi
JSON_PATH="scripts/ehrsql/assets/${DB_ID}/${SPLIT}.json"

# --- Step 1: Download data if needed ---
if [ ! -f "$JSON_PATH" ]; then
    echo "=== Downloading EHRSQL data ==="
    bash "$SCRIPT_DIR/setup.sh"
fi

# --- Step 2: Generate tasks if needed ---
if [ ! -d "$TASK_DIR/worker_0" ]; then
    echo "=== Generating tasks at $TASK_DIR ==="
    uv run python scripts/ehrsql/generate_harbor_tasks.py \
        --output-root "$TASK_DIR" \
        $JSON_FLAG "$JSON_PATH" \
        --split_task_by_n "$SPLIT_N" \
        --sample-size "$SAMPLE_SIZE" \
        --skip-evaluator
fi

# --- Step 3: Run Harbor ---
echo "=== Running Harbor job: $JOB_YAML $* ==="
uv run harbor run -c "$JOB_YAML" "$@"

# Find the latest run directory
LATEST_RUN=$(ls -td "$JOBS_DIR"/*/ 2>/dev/null | head -1)

if [ -z "$LATEST_RUN" ]; then
    echo "No run directory found in $JOBS_DIR"
    exit 1
fi

echo ""
echo "=== Aggregating results from $LATEST_RUN ==="
uv run python scripts/ehrsql/aggregate_worker_submissions.py \
    --run-dir "$LATEST_RUN" \
    --db-dir scripts/ehrsql/assets
