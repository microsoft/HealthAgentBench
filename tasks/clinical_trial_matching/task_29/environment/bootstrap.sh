#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# One-shot bootstrap container for the clinical_trial_matching benchmark.
#
# Compose starts this service, waits for it to exit cleanly, and only then
# brings the main service up (via depends_on:
# condition: service_completed_successfully). Harbor invokes
# ``docker compose up --detach --wait`` which respects this condition.
#
# Responsibilities:
#   1. Stage topic.txt and topic_id.txt from the image-baked /workspace/
#      into the shared /workspace/data/ named volume so main sees them
#      at the documented paths.
#   2. Run fetch_trials.py to populate /workspace/data/trials/ with the
#      per-topic NCT XML pool. Warm path: cache hit, no network. Cold
#      path: serialize behind a global flock over the host-mounted cache
#      so concurrent task containers don't hammer the upstream zip server.
#   3. Per-file chmod a-w on each cached XML (inside the lock) so no later
#      step — agent or otherwise — can mutate cached files.
#   4. Exit 0. Compose lets main start.
# ---------------------------------------------------------------------------

CACHE=/data/_cache
DATA=/workspace/data
TRIALS="$DATA/trials"
LOCK_DIR="$CACHE/.locks"
GLOBAL_LOCK="$LOCK_DIR/global_download.lock"

mkdir -p "$CACHE" "$LOCK_DIR" "$DATA" "$TRIALS"

# Stage the per-task text files into the shared volume (overlay would
# otherwise hide anything the Dockerfile placed at /workspace/data/).
cp /workspace/topic.txt "$DATA/topic.txt"
cp /workspace/topic_id.txt "$DATA/topic_id.txt"

# Re-grant write permissions for the lock window (a previous run may have
# chmod'd cache files read-only). Idempotent.
chmod -R u+w "$CACHE" 2>/dev/null || true

# Returns 0 if every NCT ID listed in trial_ncts.txt has a non-empty XML
# file in the cache; non-zero otherwise.
_all_cached() {
    while IFS= read -r nct; do
        nct="${nct%%#*}"
        nct="${nct//[[:space:]]/}"
        [ -z "$nct" ] && continue
        [ -f "$CACHE/${nct}.xml" ] || return 1
    done < /workspace/trial_ncts.txt
    return 0
}

_fetch() {
    python3 /workspace/fetch_trials.py \
        --ids /workspace/trial_ncts.txt \
        --out "$TRIALS" \
        --cache-dir "$CACHE" \
        --user-agent "clinical_trial_matching/1.0 (medcli benchmark)" \
        --retries 3
}

if _all_cached; then
    # Warm path: every NCT is already cached — skip global lock so all
    # containers run fully concurrently.
    _fetch
else
    # Cold path: serialize downloads behind a global lock to avoid
    # hammering the upstream server with simultaneous range requests.
    exec 9>"$GLOBAL_LOCK"
    flock 9
    _fetch
    flock -u 9  # Release before exit so other containers can proceed.
fi

# Lock cached files to read-only. Per-FILE chmod (not directory-wide) so
# concurrent task containers fetching different NCTs aren't blocked.
find "$CACHE" -maxdepth 1 -name '*.xml' -exec chmod a-w {} + 2>/dev/null || true

echo "[bootstrap] done -- main can start"
