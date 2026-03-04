#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/benchmarks/medagentbench/docker-compose.yaml"
SERVICE_NAME="fhir"
FHIR_BASE_URL="${FHIR_BASE_URL:-http://localhost:8080/fhir}"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "[fhir_up] missing compose file: ${COMPOSE_FILE}" >&2
  exit 1
fi

docker compose -f "${COMPOSE_FILE}" up -d "${SERVICE_NAME}"

container_id="$(docker compose -f "${COMPOSE_FILE}" ps -q "${SERVICE_NAME}")"
if [[ -z "${container_id}" ]]; then
  echo "[fhir_up] failed to resolve container id for service ${SERVICE_NAME}" >&2
  exit 1
fi

for _ in $(seq 1 180); do
  status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}")"
  if [[ "${status}" == "healthy" || "${status}" == "running" ]]; then
    if curl -sSf "${FHIR_BASE_URL}/metadata" >/dev/null 2>&1; then
      echo "[fhir_up] FHIR endpoint ready at ${FHIR_BASE_URL}/metadata"
      exit 0
    fi
  fi
  sleep 1
done

echo "[fhir_up] container did not become healthy in time" >&2
docker compose -f "${COMPOSE_FILE}" logs --no-color "${SERVICE_NAME}" | tail -n 50 >&2 || true
exit 1
