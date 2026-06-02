#!/bin/bash
# One-shot bootstrap container for the ct_abnormality benchmark. Compose
# starts this service, waits for it to exit cleanly, and only then brings
# the main service up (via depends_on: condition: service_completed_successfully).
#
# Responsibilities:
#   1. If /data/_cache/<volume>.nii.gz is missing, download it from Hugging
#      Face (CT-RATE; OpenRAIL-gated; needs HF_TOKEN, supplied via the
#      env_file: ../../../../.env entry in docker-compose.yaml). Freeze it
#      read-only. The whole fetch runs under a global flock so concurrent
#      task bootstraps don't hammer the CDN for the same file.
#   2. Download the validation reports CSV into the same cache (once, shared).
#   3. Derive THIS volume's gold from its report via /opt/gold_derivation.py
#      (the committed phrase rules) and write:
#         - /tests/gold.json          (verifier-only; gitignored on the host)
#         - /workspace/data/labels.txt (agent-visible label list, names only)
#      Gold is never committed to git — it is reconstructed here at run time.
#   4. Copy the volume to /workspace/data/scan.nii.gz so main sees it via the
#      shared workspace-data named volume.
#
# When this script exits 0, Compose lets main start.
set -euo pipefail

CACHE=/data/_cache
GLOBAL_LOCK="$CACHE/.bootstrap.lock"
VOLUME_NAME="valid_81_a_1.nii.gz"
HF_REPO="ibrahimhamamci/CT-RATE"
HF_PATH="dataset/valid_fixed/valid_81/valid_81_a/valid_81_a_1.nii.gz"
HF_REPORTS_PATH="dataset/radiology_text_reports/validation_reports.csv"
SRC="$CACHE/$VOLUME_NAME"
REPORTS_CSV="$CACHE/$(basename "$HF_REPORTS_PATH")"
DST=/workspace/data/scan.nii.gz

mkdir -p /workspace/data /tests "$CACHE"

_require_token() {
    if [ -z "${HF_TOKEN:-}" ]; then
        echo "[bootstrap] no Hugging Face token: HF_TOKEN is empty." 1>&2
        echo "  Accept the access agreement at https://huggingface.co/datasets/ibrahimhamamci/CT-RATE" 1>&2
        echo "  and add HF_TOKEN=hf_... to the repo-root .env file." 1>&2
        exit 2
    fi
}

# Download an HF dataset file into $CACHE/<basename> on cache miss.
_download() {
    local hf_path="$1" dest="$2"
    if [ -f "$dest" ] && [ -s "$dest" ]; then
        echo "[bootstrap] cache hit: $dest"
        return
    fi
    _require_token
    echo "[bootstrap] downloading $hf_path ..."
    HF_PATH="$hf_path" DEST="$dest" python3 - <<'PYEOF'
import os, shutil
from pathlib import Path
from huggingface_hub import hf_hub_download
token = os.environ["HF_TOKEN"].strip()
local = hf_hub_download(
    repo_id=os.environ["HF_REPO"],
    filename=os.environ["HF_PATH"],
    repo_type="dataset",
    token=token,
    local_dir=os.environ["CACHE"] + "/.hf_staging",
)
dest = Path(os.environ["DEST"])
if dest.exists() or dest.is_symlink():
    dest.unlink()
shutil.copyfile(local, dest)
PYEOF
    chmod a-w "$dest" 2>/dev/null || true
}

# Serialize cold downloads across concurrent task containers. chmod runs inside
# the critical section so files are frozen before another container races them.
export HF_REPO CACHE
exec 9>"$GLOBAL_LOCK"
flock 9
_download "$HF_PATH" "$SRC"
_download "$HF_REPORTS_PATH" "$REPORTS_CSV"
flock -u 9

# Derive this volume's gold from its report and stage the agent label list.
# Writes /tests/gold.json (gitignored host file) + /workspace/data/labels.txt.
python3 /opt/gold_derivation.py \
    --reports-csv "$REPORTS_CSV" \
    --volume "$VOLUME_NAME" \
    --out-gold /tests/gold.json \
    --out-labels /workspace/data/labels.txt

# Stage volume into the workspace-data named volume that main shares.
cp "$SRC" "$DST"

echo "[bootstrap] done — main can start"
