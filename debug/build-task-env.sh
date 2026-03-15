#!/usr/bin/env bash
# Build a Harbor task environment image using Harbor's base/build compose files
# plus the task-local compose overlay.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::compose build
