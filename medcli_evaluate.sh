#!/bin/bash
# MedCLI unified evaluation entry point.
#
# Usage:
#   bash medcli_evaluate.sh --task ehrsql --config jobs/ehrsql_eicu_test_meta.yaml
#   bash medcli_evaluate.sh --task ehrsql --config jobs/ehrsql_eicu_test_meta.yaml --model gpt-5.1-codex-mini
#   bash medcli_evaluate.sh --task ehrsql --config jobs/ehrsql_eicu_test_meta.yaml --model gpt-5.1-codex-mini --ak reasoning_effort=low
#   bash medcli_evaluate.sh --task medagentbench --config jobs/medagentbench_meta.yaml

set -euo pipefail

TASK=""
CONFIG=""
MODEL=""
HARBOR_ARGS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --task)
            TASK="$2"
            shift 2
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        *)
            HARBOR_ARGS+=("$1")
            shift
            ;;
    esac
done

if [ -z "$TASK" ] || [ -z "$CONFIG" ]; then
    echo "Usage: $0 --task <benchmark> --config <job-yaml> [--model <model_name>] [harbor run flags...]"
    echo ""
    echo "Arguments:"
    echo "  --task      Benchmark name (ehrsql, medagentbench)"
    echo "  --config    Path to Harbor job YAML config"
    echo "  --model     Model name override (optional)"
    echo "  Additional flags are passed directly to 'harbor run'"
    exit 1
fi

# Build harbor run flags
if [ -n "$MODEL" ]; then
    HARBOR_ARGS=("-m" "$MODEL" "${HARBOR_ARGS[@]}")
fi

# Delegate to benchmark-specific script
SCRIPT="scripts/${TASK}/run_and_evaluate.sh"

if [ ! -f "$SCRIPT" ]; then
    echo "Error: No run script found for task '$TASK' (expected $SCRIPT)"
    exit 1
fi

bash "$SCRIPT" "$CONFIG" "${HARBOR_ARGS[@]}"
