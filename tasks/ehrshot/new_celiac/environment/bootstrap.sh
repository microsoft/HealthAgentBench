#!/bin/bash
# One-shot bootstrap container for the ehrshot benchmark. Compose starts this
# service, waits for it to exit cleanly, and only then brings the main
# service up (via depends_on: condition: service_completed_successfully).
#
# Responsibilities:
#   1. If /data/_cache/EHRSHOT_ASSETS/ is missing the key bundle files,
#      download and extract EHRSHOT_ASSETS.zip from Redivis (gated on a
#      long-lived API token mounted at /root/.redivis/api_token).
#      Cache-hit is detected by file presence -- no marker file written.
#   2. Stage this task's data into /workspace/data/ via the shared
#      workspace-data named volume.
#
# When this script exits 0, Compose lets main start.
set -euo pipefail

TASK_ID="new_celiac"
CACHE=/data/_cache
ASSETS="$CACHE/EHRSHOT_ASSETS"
GLOBAL_LOCK="$CACHE/.bootstrap.lock"
TOKEN_FILE=/root/.redivis/api_token

mkdir -p "$CACHE" /workspace/data /workspace/submission

# Cache-hit check: presence of the key bundle files. Treat the cache as
# valid if these are all non-empty. This works whether the host pre-
# populated the bundle (via scripts/ehrshot/download.py) or a previous
# bootstrap run downloaded it -- no marker file needed.
_cache_ok() {
    [ -s "$ASSETS/data/ehrshot.csv" ] \
        && [ -s "$ASSETS/splits/person_id_map.csv" ] \
        && [ -s "$ASSETS/features/count_features.pkl" ]
}

_fetch() {
    if _cache_ok; then
        echo "[bootstrap] cache hit: $ASSETS"
        return
    fi
    if [ ! -f "$TOKEN_FILE" ] || [ ! -s "$TOKEN_FILE" ]; then
        echo "[bootstrap] no Redivis API token at $TOKEN_FILE." 1>&2
        echo "  Accept the EHRSHOT data-use agreement at" 1>&2
        echo "  https://redivis.com/datasets/53gc-8rhx41kgt and write your" 1>&2
        echo "  token to ~/.redivis/api_token on the host." 1>&2
        exit 2
    fi
    echo "[bootstrap] cache miss; downloading EHRSHOT_ASSETS.zip from Redivis (~4 GB)..."
    REDIVIS_API_TOKEN="$(cat "$TOKEN_FILE")" python3 - <<'PYEOF'
import os, sys, zipfile, shutil
from pathlib import Path
import redivis
token = os.environ["REDIVIS_API_TOKEN"].strip()
if hasattr(redivis, "set_api_token"):
    try: redivis.set_api_token(token)
    except Exception: pass
cache = Path("/data/_cache")
zpath = cache / "EHRSHOT_ASSETS.zip"
table = redivis.table("shahlab.ehrshot:53gc:v3_0.files:4avd")
table.file("EHRSHOT_ASSETS.zip").download(str(cache), overwrite=True)
print(f"[bootstrap] extracting {zpath} -> {cache}", file=sys.stderr)
with zipfile.ZipFile(zpath) as z:
    z.extractall(cache)
zpath.unlink(missing_ok=True)
macosx = cache / "__MACOSX"
if macosx.is_dir():
    shutil.rmtree(macosx)
PYEOF
}

# Serialize cold downloads across concurrent task containers. (Cache-hit
# branch is also serialized but exits in well under a second.)
exec 9>"$GLOBAL_LOCK"
flock 9
_fetch
flock -u 9

# Per-task data slicing. Writes the agent-visible artifacts to
# /workspace/data/ AND writes the verifier-only test_labels.csv into
# /tests/ (RW-mounted from host tasks/<task>/tests/; main does NOT see
# /tests/ during agent runtime per Harbor's default).
python3 /opt/ehrshot/stage_data.py --task-id "$TASK_ID" \
    --test-subset last \
    --private /tests

echo "[bootstrap] done -- main can start"
