#!/bin/bash
set -euo pipefail

SOURCE=/data/_cache/panc_dx_1st_seq_OS.csv

if [ ! -s "$SOURCE" ]; then
    # Pin public source data so upstream changes cannot alter benchmark inputs.
    URL="https://raw.githubusercontent.com/clinical-data-mining/msk-chord-figures-public/6463b36a2de2f7355f616d155c8791052cb98efd/data/${SOURCE##*/}"
    mkdir -p /data/_cache
    PARTIAL="$(mktemp "${SOURCE}.part.XXXXXX")"
    trap 'rm -f "$PARTIAL"' EXIT
    echo "[bootstrap] Downloading public MSK-CHORD PANC cohort..."
    curl --fail --location --silent --show-error \
        --connect-timeout 20 --max-time 120 --retry 3 \
        --output "$PARTIAL" "$URL"
    echo "77cc2d77f17f97bbec34fd310554e4894db2fc137210203e13d71507858a5838  $PARTIAL" | sha256sum --check --status
    chmod 644 "$PARTIAL"
    mv "$PARTIAL" "$SOURCE"
    trap - EXIT
fi

mkdir -p /workspace/data /workspace/submission /tests

python3 /opt/survival_prediction/stage_data.py \
    --source-dir /data/_cache \
    --workspace-dir /workspace/data \
    --private-dir /tests

echo "[bootstrap] staged MSK-CHORD PANC TTE_OS fold 0"
