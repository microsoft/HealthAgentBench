#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

export MEDCLI_TUMOR_PATH_CACHE_ROOT="${MEDCLI_TUMOR_PATH_CACHE_ROOT:-${HOME}/harbor-cache/tumor_area_selection_pathology}"

uv run python scripts/tumor_area_selection_pathology/setup_assets.py "$@"
