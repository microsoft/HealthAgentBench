#!/bin/bash
set -euo pipefail
mkdir -p /cache /task-data
# Serialize first-time download/build across all compositional-QA tasks and concurrent trials.
(
  flock -x 9
  if [[ ! -s /cache/mimic4-demo-v2.2.duckdb ]]; then
    echo "[bootstrap] Downloading public MIMIC-IV-demo v2.2 and building raw tables"
    python3 /opt/bootstrap/stage_data.py --output-db /cache/mimic4-demo-v2.2.duckdb.tmp
    mv /cache/mimic4-demo-v2.2.duckdb.tmp /cache/mimic4-demo-v2.2.duckdb
  else
    echo "[bootstrap] Using cached raw MIMIC-IV-demo v2.2 database"
  fi
  cp /cache/mimic4-demo-v2.2.duckdb /task-data/mimic4.db
) 9>/cache/.bootstrap.lock
chmod 0444 /task-data/mimic4.db
echo "[bootstrap] Raw database ready; no test labels staged"
