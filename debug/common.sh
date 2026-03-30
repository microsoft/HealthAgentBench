#!/usr/bin/env bash
# Common shell helpers shared by Harbor debug scripts.
# These helpers derive Harbor's compose inputs from a task directory and mirror
# Harbor's docker environment defaults closely enough for local debugging.
set -euo pipefail

hb::repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

hb::task_name() {
  basename "${HB_TASK_DIR}"
}

hb::instruction_path() {
  echo "${HB_TASK_DIR_ABS}/instruction.md"
}

# Fail fast when a required environment variable is missing.
hb::require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "missing required env var: ${name}" >&2
    exit 1
  fi
}

hb::codex_auth_file() {
  local path="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
  if [[ ! -f "${path}" ]]; then
    echo "missing Codex auth file: ${path}" >&2
    echo "set CODEX_AUTH_FILE or login with codex to populate ~/.codex/auth.json" >&2
    exit 1
  fi
  echo "${path}"
}

# Read one value from the task's task.toml [environment] section.
hb::task_config_value() {
  local key="$1"
  local toml_path="${HB_TASK_DIR_ABS}/task.toml"
  python - "$toml_path" "$key" <<'PY'
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

payload = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = payload.get("environment", {}).get(sys.argv[2], "")
print(value)
PY
}

# Populate compose-related environment variables for the selected Harbor task.
hb::setup_task_env() {
  : "${HB_TASK_DIR:=tasks/medagentbench}"
  : "${HB_PROJECT_NAME:=$(basename "${HB_TASK_DIR}")-debug}"
  : "${HB_MAIN_SERVICE:=main}"
  : "${HB_TMP_ROOT:=$(hb::repo_root)/.tmp/${HB_PROJECT_NAME}}"

  local repo_root
  repo_root="$(hb::repo_root)"
  export HB_REPO_ROOT="${repo_root}"

  export HB_TASK_DIR_ABS="${repo_root}/${HB_TASK_DIR}"
  export HB_ENV_DIR="${HB_TASK_DIR_ABS}/environment"
  export HB_BASE_COMPOSE="${repo_root}/.venv/lib/python3.12/site-packages/harbor/environments/docker/docker-compose-base.yaml"
  export HB_BUILD_COMPOSE="${repo_root}/.venv/lib/python3.12/site-packages/harbor/environments/docker/docker-compose-build.yaml"
  export HB_TASK_COMPOSE="${HB_ENV_DIR}/docker-compose.yaml"
  : "${HB_MAIN_IMAGE_NAME:=hb__$(hb::task_name)}"

  export MAIN_IMAGE_NAME="${HB_MAIN_IMAGE_NAME}"
  export CONTEXT_DIR="${HB_ENV_DIR}"
  export HOST_VERIFIER_LOGS_PATH="${HB_TMP_ROOT}/verifier"
  export HOST_AGENT_LOGS_PATH="${HB_TMP_ROOT}/agent"
  export HOST_ARTIFACTS_PATH="${HB_TMP_ROOT}/artifacts"
  export ENV_VERIFIER_LOGS_PATH="/logs/verifier"
  export ENV_AGENT_LOGS_PATH="/logs/agent"
  export ENV_ARTIFACTS_PATH="/artifacts"
  local task_cpus task_memory_mb
  task_cpus="$(hb::task_config_value cpus)"
  task_memory_mb="$(hb::task_config_value memory_mb)"
  export CPUS="${HB_CPUS:-${task_cpus:-1}}"
  export MEMORY="${HB_MEMORY:-${task_memory_mb:-2048}M}"

  mkdir -p "${HOST_VERIFIER_LOGS_PATH}" "${HOST_AGENT_LOGS_PATH}" "${HOST_ARTIFACTS_PATH}"
}

# Run docker compose with the same file layering Harbor uses for docker tasks.
hb::compose() {
  hb::setup_task_env
  docker compose \
    -p "${HB_PROJECT_NAME}" \
    --project-directory "${HB_ENV_DIR}" \
    -f "${HB_BASE_COMPOSE}" \
    -f "${HB_BUILD_COMPOSE}" \
    -f "${HB_TASK_COMPOSE}" \
    "$@"
}

# Fail if the task's main service is not currently running.
hb::require_running_main() {
  hb::setup_task_env
  local running
  running="$(hb::compose ps --services --status running 2>/dev/null || true)"
  if ! grep -qx "${HB_MAIN_SERVICE}" <<<"${running}"; then
    echo "task environment is not running: ${HB_MAIN_SERVICE}" >&2
    echo "start it first with: bash debug/up-task-env.sh" >&2
    exit 1
  fi
}

# Copy the task instruction into the live main container for manual agent runs.
hb::stage_instruction_in_container() {
  hb::setup_task_env
  local target_path="${1:-/tmp/hb-task-instruction.md}"
  local source_path
  source_path="$(hb::instruction_path)"
  if [[ ! -f "${source_path}" ]]; then
    echo "missing task instruction: ${source_path}" >&2
    exit 1
  fi
  hb::compose cp "${source_path}" "${HB_MAIN_SERVICE}:${target_path}"
}

hb::latest_harbor_run() {
  local jobs_dir="${1:-results}"
  ls -td "${jobs_dir}"/* 2>/dev/null | head -n 1
}

hb::latest_trial_dir() {
  local run_dir="$1"
  local task_name
  task_name="$(hb::task_name)"
  find "${run_dir}" -maxdepth 1 -type d -name "${task_name}__*" | sort | head -n 1
}
