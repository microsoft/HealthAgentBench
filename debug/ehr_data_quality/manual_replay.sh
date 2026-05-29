#!/bin/bash
# Local manual replay of one ehr_data_quality task.
#
# Stages corrupted data, runs the heuristic reference solver, runs the
# verifier, and prints F1. This is the canonical "is the task replayable?"
# check from the benchmark addition workflow — it distinguishes agent
# failures from task / verifier failures.
#
# Usage:
#   bash debug/ehr_data_quality/manual_replay.sh                          # all 4 tasks
#   bash debug/ehr_data_quality/manual_replay.sh task_impossible_value    # one task
#
# Prerequisite: scripts/ehr_data_quality/assets/raw_cache/ must contain the
# pristine MIMIC-IV-demo CSVs. Pre-populate it once with:
#
#   uv run python -c "
#   from pathlib import Path; import sys
#   sys.path.insert(0, 'scripts/ehr_data_quality')
#   from stage_data import _download_all
#   _download_all(Path('scripts/ehr_data_quality/assets/raw_cache'))"

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RAW_CACHE="scripts/ehr_data_quality/assets/raw_cache"
if [[ ! -d "$RAW_CACHE/hosp" ]]; then
    echo "ERROR: $RAW_CACHE not populated. See header comment for one-time setup." >&2
    exit 2
fi

run_one_task() {
    local task_id="$1"
    local cfg="tasks/ehr_data_quality/${task_id}/environment/workspace/task_config.yaml"
    if [[ ! -f "$cfg" ]]; then
        echo "ERROR: task config not found: $cfg" >&2
        echo "Run: uv run python scripts/ehr_data_quality/generate_harbor_tasks.py" >&2
        return 2
    fi

    local labels="tasks/ehr_data_quality/${task_id}/tests/labels.csv"
    local work="/tmp/dq_replay/${task_id}"
    rm -rf "$work"
    mkdir -p "$work/data" "$work/submission" "$work/logs/verifier"

    # 1) Stage corrupted data using the same pipeline the Dockerfile runs.
    uv run python scripts/ehr_data_quality/stage_data.py \
        --config "$cfg" \
        --output-dir "$work/data" \
        --input-dir "$RAW_CACHE" \
        --no-duckdb \
        --verify-against "$labels" \
        > "$work/stage.log" 2>&1

    # 2) Run the heuristic reference solver against the corrupted CSVs.
    uv run python scripts/ehr_data_quality/reference_solver.py \
        --data-dir "$work/data" \
        --output "$work/submission/flagged_rows.csv" \
        > "$work/solver.log" 2>&1

    # 3) Score with the verifier.
    uv run python -c "
import json, sys
from pathlib import Path
sys.path.insert(0, 'scripts/ehr_data_quality')
from harbor_evaluator import evaluate
f1 = evaluate(
    Path('$work/submission/flagged_rows.csv'),
    Path('$labels'),
    Path('$work/logs/verifier'),
)
m = json.loads(Path('$work/logs/verifier/metrics.json').read_text())
print(f'$task_id  f1={f1:.4f}  recall={m[\"recall\"]:.4f}  precision={m[\"precision\"]:.4f}  '
      f'flagged={m[\"n_flagged_rows\"]}  useful={m[\"n_useful_flagged_rows\"]}  '
      f'clusters={m[\"n_clusters_caught\"]}/{m[\"n_clusters\"]}')
"
}

if [[ $# -ge 1 ]]; then
    run_one_task "$1"
else
    for tid in task_impossible_value task_inconsistency task_demographic_conflict task_combined; do
        run_one_task "$tid"
    done
fi
