#!/usr/bin/env bash
# Open an interactive shell in the running Harbor task main container.
# The task environment must already be up.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
hb::compose exec "${HB_MAIN_SERVICE}" bash
