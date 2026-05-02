#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Bootstrap the per-topic clinical-trial corpus.
#
# Mounts:
#   /data/_cache  -- host-side cache (rw). Shared across concurrent task
#                    containers; we hold a per-topic flock during writes.
#
# Behaviour:
#   1. Re-make the cache writable (a previous run may have chmod'd it ro).
#   2. Acquire a per-topic flock under /data/_cache/.locks/topic_<id>.lock.
#   3. Run fetch_trials.py with --cache-dir=/data/_cache. It pulls cache
#      hits (no network) and downloads the rest from the upstream zip
#      snapshot, writing back into /data/_cache (chmod a-w per file).
#   4. Chmod -R a-w /data/_cache so the agent cannot mutate cached files.
#   5. Release flock, exec the agent.
# ---------------------------------------------------------------------------

CACHE=/data/_cache
TRIALS=/workspace/data/trials
TOPIC_ID="$(cat /workspace/data/topic_id.txt)"
LOCK_DIR="$CACHE/.locks"
LOCK_FILE="$LOCK_DIR/topic_${TOPIC_ID}.lock"

mkdir -p "$CACHE" "$LOCK_DIR" "$TRIALS"

# Re-grant write permissions for the lock window. (chmod is idempotent.)
chmod -R u+w "$CACHE" 2>/dev/null || true

exec 9>"$LOCK_FILE"
flock 9

python3 /workspace/fetch_trials.py \
    --ids /workspace/trial_ncts.txt \
    --out "$TRIALS" \
    --cache-dir "$CACHE" \
    --user-agent "clinical_trial_matching/1.0 (medcli benchmark)" \
    --retries 3

# Lock the cache to read-only so neither the agent nor any later step can
# mutate cached files. Tolerant to filesystem oddities.
chmod -R a-w "$CACHE" 2>/dev/null || true

# Lock released when fd 9 closes at shell exit. Now exec what Harbor wants.
exec "$@"
