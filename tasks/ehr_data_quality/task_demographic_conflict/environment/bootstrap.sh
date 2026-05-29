#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Stage the corrupted MIMIC-IV-demo subset for this task.
#
# Inputs (bind-mounted into bootstrap, NEVER into main):
#   /opt/bootstrap_inputs/inject.py
#   /opt/bootstrap_inputs/stage_data.py
#   /opt/bootstrap_inputs/task_config.yaml
#   /tests/labels.csv                     (gold, read-only — single source
#                                          of truth shared with the verifier)
#
# Output (named volume shared with main):
#   /workspace/data/csv/<table>.csv.gz    (eight EHR tables, partially corrupted)
#
# Cross-trial cache (host bind-mount):
#   /data/_src/raw_cache                  (MIMIC-IV-demo raw CSVs)
# ---------------------------------------------------------------------------

LOCK_DIR=/data/_src/raw_cache/.bootstrap.locks
mkdir -p "$LOCK_DIR"

# Global lock: concurrent trials share the raw_cache download. First trial to
# acquire the lock fills the cache; others wait, then read from it.
exec 9>"$LOCK_DIR/global.lock"
flock 9

# Run the corruption pipeline. --input-dir reuses the bind-mounted raw_cache
# so the MIMIC-IV-demo download happens at most once per host. --verify-against
# asserts the freshly-corrupted data matches the gold labels.csv bit-for-bit;
# if inject.py drifts from labels.csv this fails loudly and Harbor aborts the
# trial before the agent ever starts (preventing silently-broken runs).
python /opt/bootstrap_inputs/stage_data.py \
    --config /opt/bootstrap_inputs/task_config.yaml \
    --output-dir /workspace/data \
    --input-dir /data/_src/raw_cache \
    --verify-against /tests/labels.csv \
    --no-duckdb

echo "[bootstrap] corrupted data staged at /workspace/data, verify-against passed."
