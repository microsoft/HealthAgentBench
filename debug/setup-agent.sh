#!/usr/bin/env bash
# Set up the default debug agent inside the running Harbor task container.
# This is the orchestration layer above install/prepare primitives.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
hb::require_running_main

: "${HB_DEFAULT_AGENT:=codex}"

case "${HB_DEFAULT_AGENT}" in
  codex)
    hb::require_var CODEX_AUTH_JSON
    bash "$(dirname "$0")/install-codex-agent.sh"
    bash "$(dirname "$0")/prepare-codex-agent.sh"
    ;;
  *)
    echo "unsupported default agent: ${HB_DEFAULT_AGENT}" >&2
    echo "supported values: codex" >&2
    exit 1
    ;;
esac
