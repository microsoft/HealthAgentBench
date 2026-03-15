#!/usr/bin/env bash
# Stop and remove the Harbor task debug Docker Compose stack.
# Set HB_FULL_CLEANUP=1 to also remove images and volumes, similar to Harbor's
# heavier cleanup path.
set -euo pipefail
source "$(dirname "$0")/common.sh"

if [[ "${HB_FULL_CLEANUP:-0}" == "1" ]]; then
  hb::compose down --rmi all --volumes --remove-orphans
else
  hb::compose down --remove-orphans
fi
