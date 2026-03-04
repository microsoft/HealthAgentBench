#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/ehr_medagentbench_fhir_mock.pid"

if [[ -f "${PID_FILE}" ]]; then
  pid="$(cat "${PID_FILE}")"
  if kill -0 "${pid}" 2>/dev/null; then
    kill "${pid}" || true
  fi
  rm -f "${PID_FILE}"
  echo "[fhir_down] stopped mock FHIR service"
else
  echo "[fhir_down] no running mock FHIR service"
fi
