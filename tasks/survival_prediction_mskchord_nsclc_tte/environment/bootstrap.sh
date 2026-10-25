#!/bin/bash
set -euo pipefail

SOURCE=/data/_cache/nsclc_dx_1st_seq_OS.csv

if [ ! -s "$SOURCE" ]; then
    # Pin public source data so upstream changes cannot alter benchmark inputs.
    URL="https://raw.githubusercontent.com/clinical-data-mining/msk-chord-figures-public/6463b36a2de2f7355f616d155c8791052cb98efd/data/${SOURCE##*/}"
    mkdir -p /data/_cache
    PARTIAL="$(mktemp "${SOURCE}.part.XXXXXX")"
    trap 'rm -f "$PARTIAL"' EXIT
    echo "[bootstrap] Downloading public MSK-CHORD NSCLC cohort..."
    curl --fail --location --silent --show-error \
        --connect-timeout 20 --max-time 120 --retry 3 \
        --output "$PARTIAL" "$URL"
    echo "7f160869cf8f401c960353beca5933375229d282ed130b6e24202b9c3e84573f  $PARTIAL" | sha256sum --check --status
    chmod 644 "$PARTIAL"
    mv "$PARTIAL" "$SOURCE"
    trap - EXIT
fi

mkdir -p /workspace/data /workspace/submission /tests

python3 /opt/survival_prediction/stage_data.py \
    --source-dir /data/_cache \
    --workspace-dir /workspace/data \
    --private-dir /tests

echo "[bootstrap] staged MSK-CHORD NSCLC TTE_OS fold 0"
