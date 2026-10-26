#!/bin/bash
# One-shot bootstrap container for an mri_qa task. Compose starts this
# service, waits for it to exit cleanly, and only then brings the main
# service up (depends_on: condition: service_completed_successfully).
#
# Mounts (bootstrap service ONLY; none of these reach the agent's main
# container):
#   /opt/task_manifest.json  this exam's Redivis file entries + pinned
#                            checksums (no answers)
#   /opt/stage_mri.py        the staging/gold-derivation script
#   /data/_cache             host-side cross-trial cache
#                            (assets/mri_qa/assets/raw_cache; gitignored)
#   /tests                   host tasks/<task>/tests/, RW: gold.json and
#                            data_verification.json are written here at run
#                            time (gitignored). Harbor builds the separate
#                            verifier image from this dir at verification time.
#   /workspace/mri           named volume shared with main (read-only there)
#
# REDIVIS_API_TOKEN comes from the repo-root .env via the compose env_file
# entry and is only needed on a cache miss. After this script exits the
# token, the manifest, and the raw cache are gone from the trial.
set -euo pipefail

mkdir -p /data/_cache /workspace/mri /tests

python3 /opt/stage_mri.py \
    --manifest /opt/task_manifest.json \
    --cache /data/_cache \
    --workspace /workspace/mri \
    --tests /tests

echo "[bootstrap] done — main can start"
