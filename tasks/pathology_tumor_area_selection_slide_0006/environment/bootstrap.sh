#!/bin/bash
# One-shot bootstrap container. Compose starts this service, waits for it to
# exit cleanly, and only then brings main up (depends_on:
# condition: service_completed_successfully).
#
# It fetches this task's slide from upstream into a shared cross-run cache and
# stages it into the shared volume that main reads. The download URL and source
# name live ONLY in this file, which is bind-mounted into the bootstrap service
# — never baked into the image — so the agent can never read them. The hidden
# tumor mask is verifier-only and is fetched by the verifier, not here.
set -euo pipefail

TASK_ID="slide_0006"
EXT=".tif"
DOWNLOAD_URL="https://camelyon-dataset.s3.amazonaws.com/CAMELYON16/images/tumor_047.tif"
TILE_SIZE="256"
ANALYSIS_DOWNSAMPLE="16"

CACHE=/data/_cache
GLOBAL_LOCK="$CACHE/.bootstrap.lock"
SRC="$CACHE/${TASK_ID}${EXT}"
DEST_DIR=/data/slide/current
DEST="$DEST_DIR/slide${EXT}"

mkdir -p "$CACHE" "$DEST_DIR"

# Serialize cold downloads across concurrent task containers sharing the cache.
exec 9>"$GLOBAL_LOCK"
flock 9
if [ ! -s "$SRC" ]; then
    echo "[bootstrap] downloading slide ..."
    curl -fSL --retry 3 -o "$SRC.part" "$DOWNLOAD_URL"
    mv "$SRC.part" "$SRC"
fi
flock -u 9

# Stage the slide (cached under the opaque task id) into the shared volume and
# write the public manifest. Neither names the upstream dataset.
cp "$SRC" "$DEST"
cat > "$DEST_DIR/manifest.json" <<JSON
{
  "task_id": "$TASK_ID",
  "tile_size": $TILE_SIZE,
  "analysis_downsample": $ANALYSIS_DOWNSAMPLE,
  "slide_path": "/data/slide/current/slide${EXT}"
}
JSON

echo "[bootstrap] done — main can start"
