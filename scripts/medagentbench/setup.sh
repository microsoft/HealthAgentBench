#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASSET_DIR="${ROOT_DIR}/benchmarks/medagentbench/assets"
TASKS_JSON="${ASSET_DIR}/tasks.json"

mkdir -p "${ASSET_DIR}"

if [[ -f "${TASKS_JSON}" ]]; then
  echo "[setup] assets already present: ${TASKS_JSON}"
  exit 0
fi

cat > "${TASKS_JSON}" <<'JSON'
[
  {
    "task_id": "mab_001",
    "category": "cohort_construction",
    "difficulty": "easy",
    "instruction": "Find patients older than 65 with at least one inpatient encounter in the last year.",
    "expected_answer": "A cohort list with patient identifiers",
    "required_actions": [],
    "split": "std",
    "task_type": "query",
    "backend_profile": "fhir"
  }
]
JSON

echo "[setup] wrote sample assets: ${TASKS_JSON}"
