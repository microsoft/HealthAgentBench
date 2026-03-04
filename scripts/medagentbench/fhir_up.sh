#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="/tmp/ehr_medagentbench_fhir_mock.pid"
LOG_FILE="/tmp/ehr_medagentbench_fhir_mock.log"

if [[ -f "${PID_FILE}" ]]; then
  pid="$(cat "${PID_FILE}")"
  if kill -0 "${pid}" 2>/dev/null; then
    echo "[fhir_up] mock FHIR already running (pid=${pid})"
  else
    rm -f "${PID_FILE}"
  fi
fi

if ! curl -sSf "http://localhost:8080/metadata" >/dev/null 2>&1; then
  nohup "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/medagentbench/fhir_mock_server.py" >"${LOG_FILE}" 2>&1 &
  echo $! > "${PID_FILE}"
fi

for _ in $(seq 1 30); do
  if curl -sSf "http://localhost:8080/metadata" >/dev/null 2>&1; then
    echo "[fhir_up] FHIR endpoint ready at http://localhost:8080/metadata"
    exit 0
  fi
  sleep 1
done

echo "[fhir_up] failed to start FHIR endpoint" >&2
exit 1
