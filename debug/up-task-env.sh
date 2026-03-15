#!/usr/bin/env bash
# Start a Harbor task environment and wait for services to become ready.
# This intentionally performs a light cleanup first to match Harbor's normal
# docker startup behavior.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::compose down --remove-orphans || true
hb::compose up -d --wait
hb::compose ps
