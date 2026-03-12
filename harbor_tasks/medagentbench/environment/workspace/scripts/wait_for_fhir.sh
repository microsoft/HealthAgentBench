#!/usr/bin/env bash
set -euo pipefail

base_url="${FHIR_BASE_URL:-http://fhir:8080/fhir}"
for _ in $(seq 1 60); do
  if curl -fsS "${base_url}/metadata" >/dev/null 2>&1; then
    echo "FHIR is ready at ${base_url}"
    exit 0
  fi
  sleep 2
done
echo "FHIR was not ready in time: ${base_url}" >&2
exit 1
