#!/bin/bash
set -euo pipefail

SOURCE=/data/_cache/panc_dx_1st_seq_OS.csv

if [ ! -s "$SOURCE" ]; then
    echo "[bootstrap] missing MSK-CHORD PANC data: $SOURCE" 1>&2
    echo "Place panc_dx_1st_seq_OS.csv in assets/survival_prediction/mskchord/." 1>&2
    exit 2
fi

mkdir -p /workspace/data /workspace/submission /tests

python3 /opt/survival_prediction/stage_data.py \
    --source-dir /data/_cache \
    --workspace-dir /workspace/data \
    --private-dir /tests

echo "[bootstrap] staged MSK-CHORD PANC SURV_PROB fold 0"
