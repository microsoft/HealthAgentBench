#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Bootstrap the per-topic clinical-trial corpus.
#
# Mounts:
#   /data/_cache  -- host-side cache (rw). Shared across concurrent task
#                    containers.
#
# Behaviour:
#   1. Re-make the cache writable (a previous run may have chmod'd it ro).
#   2. Check if all NCTs for this topic are already in the cache.
#      - Warm path (all cached): run fetch_trials.py directly; pure cache
#        hits, no network, no global lock needed.
#      - Cold path (any missing): acquire a global download lock so that
#        concurrent containers serialize network downloads and do not
#        overwhelm the upstream zip server with simultaneous range requests.
#        Release the lock as soon as fetch_trials.py returns, before the
#        agent starts, so other containers can proceed in parallel.
#   3. Chmod -R a-w /data/_cache so the agent cannot mutate cached files.
#   4. Exec the agent.
# ---------------------------------------------------------------------------

CACHE=/data/_cache
TRIALS=/workspace/data/trials
LOCK_DIR="$CACHE/.locks"
GLOBAL_LOCK="$LOCK_DIR/global_download.lock"

mkdir -p "$CACHE" "$LOCK_DIR" "$TRIALS"

# Signal to Harbor agent setup that bootstrap is in progress.
# The Codex wrapper polls for .bootstrap_done before starting the agent.
touch /workspace/.bootstrap_required

# Re-grant write permissions for the lock window. (chmod is idempotent.)
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
    flock -u 9  # Release before exec so other containers can proceed.
fi

# Lock the cache to read-only so neither the agent nor any later step can
# mutate cached files. Tolerant to filesystem oddities.
chmod -R a-w "$CACHE" 2>/dev/null || true

# Signal that bootstrap is complete; the Codex setup_command will unblock.
touch /workspace/.bootstrap_done

exec "$@"
