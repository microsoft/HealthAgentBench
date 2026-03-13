#!/usr/bin/env bash
set -euo pipefail

base_url="${FHIR_BASE_URL:-http://fhir:8080/fhir}"
until curl -fsS "${base_url}/metadata" >/dev/null; do
  sleep 1
done
echo "FHIR ready: ${base_url}"
