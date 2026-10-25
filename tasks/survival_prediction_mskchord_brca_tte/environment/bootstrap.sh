#!/bin/bash
set -euo pipefail

SOURCE=/data/_cache/brca_dx_1st_seq_OS.csv

if [ ! -s "$SOURCE" ]; then
    # Pin public source data so upstream changes cannot alter benchmark inputs.
    URL="https://raw.githubusercontent.com/clinical-data-mining/msk-chord-figures-public/6463b36a2de2f7355f616d155c8791052cb98efd/data/${SOURCE##*/}"
    mkdir -p /data/_cache
    PARTIAL="$(mktemp "${SOURCE}.part.XXXXXX")"
    trap 'rm -f "$PARTIAL"' EXIT
    echo "[bootstrap] Downloading public MSK-CHORD BRCA cohort..."
    curl --fail --location --silent --show-error \
        --connect-timeout 20 --max-time 120 --retry 3 \
        --output "$PARTIAL" "$URL"
    echo "fbf2e19a986cc5a76d90af2c0d92ee55172b343d62ceba72e956baec197237be  $PARTIAL" | sha256sum --check --status
    chmod 644 "$PARTIAL"
    mv "$PARTIAL" "$SOURCE"
    trap - EXIT
fi

mkdir -p /workspace/data /workspace/submission /tests

python3 /opt/survival_prediction/stage_data.py \
    --source-dir /data/_cache \
    --workspace-dir /workspace/data \
    --private-dir /tests

echo "[bootstrap] staged MSK-CHORD BRCA TTE_OS fold 0"
