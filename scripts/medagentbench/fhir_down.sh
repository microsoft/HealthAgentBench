#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/benchmarks/medagentbench/docker-compose.yaml"
SERVICE_NAME="fhir"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "[fhir_down] missing compose file: ${COMPOSE_FILE}" >&2
  exit 1
fi

docker compose -f "${COMPOSE_FILE}" down --remove-orphans

echo "[fhir_down] stopped compose service ${SERVICE_NAME}"
