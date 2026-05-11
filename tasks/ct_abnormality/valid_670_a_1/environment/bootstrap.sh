#!/bin/bash
# One-shot bootstrap container for the ct_abnormality benchmark. Compose
# starts this service, waits for it to exit cleanly, and only then brings
# the main service up (via depends_on: condition: service_completed_successfully).
#
# Responsibilities:
#   1. Stage the per-task labels list to /workspace/data/labels.txt.
#   2. If /data/_cache/<volume>.nii.gz is missing, download it from Hugging
#      Face (CT-RATE; OpenRAIL-gated; needs host token at
#      /root/.cache/huggingface/token).
#   3. Freeze the just-downloaded volume read-only (per-file chmod a-w,
#      under a global flock so concurrent fetches of *different* volumes
#      into the same cache dir don't block each other).
#   4. Copy the volume to /workspace/data/scan.nii.gz so main sees it
#      via the shared workspace-data named volume.
#
# When this script exits 0, Compose lets main start.
set -euo pipefail

CACHE=/data/_cache
GLOBAL_LOCK="$CACHE/.bootstrap.lock"
VOLUME_NAME="valid_670_a_1.nii.gz"
HF_REPO="ibrahimhamamci/CT-RATE"
HF_PATH="dataset/valid_fixed/valid_670/valid_670_a/valid_670_a_1.nii.gz"
SRC="$CACHE/$VOLUME_NAME"
DST=/workspace/data/scan.nii.gz

mkdir -p /workspace/data "$CACHE"

# Stage labels.txt up-front (no network needed).
cat > /workspace/data/labels.txt <<'__LABELS_EOF__'
Cardiomegaly
Pericardial effusion
Lymphadenopathy
Lung nodule
__LABELS_EOF__

_fetch() {
    if [ -f "$SRC" ] && [ -s "$SRC" ]; then
        echo "[bootstrap] cache hit: $SRC"
        return
    fi
    if [ ! -f /root/.cache/huggingface/token ]; then
        echo "[bootstrap] no Hugging Face token at /root/.cache/huggingface/token." 1>&2
        echo "  Accept the access agreement at https://huggingface.co/datasets/ibrahimhamamci/CT-RATE" 1>&2
        echo "  and run 'huggingface-cli login' on the host." 1>&2
        exit 2
    fi
    echo "[bootstrap] downloading $HF_PATH ..."
    python3 - <<PYEOF
import shutil
from pathlib import Path
from huggingface_hub import hf_hub_download

token = Path('/root/.cache/huggingface/token').read_text().strip()
local = hf_hub_download(
    repo_id="$HF_REPO",
    filename="$HF_PATH",
    repo_type='dataset',
    token=token,
    local_dir="$CACHE/.hf_staging",
)
src = Path(local)
dst = Path("$SRC")
if dst.exists() or dst.is_symlink():
    dst.unlink()
shutil.copyfile(src, dst)
PYEOF
    # Freeze the just-downloaded file read-only. Per-FILE chmod (not
    # directory-wide) so concurrent bootstraps fetching *different*
    # volumes into the same cache dir aren't blocked.
    chmod a-w "$SRC" 2>/dev/null || true
}

# Serialize cold downloads across concurrent task containers (one bootstrap
# per task can be running). The chmod runs inside this critical section so
# the file is frozen before another container can race against the same path.
exec 9>"$GLOBAL_LOCK"
flock 9
_fetch
flock -u 9

# Stage volume into the workspace-data named volume that main shares.
cp "$SRC" "$DST"

echo "[bootstrap] done — main can start"
