#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASSET_DIR="${ROOT_DIR}/benchmarks/medagentbench/assets"
TASKS_JSON="${ASSET_DIR}/tasks.json"
CHECKSUMS_FILE="${ASSET_DIR}/SHA256SUMS"

mkdir -p "${ASSET_DIR}"

if [[ ! -f "${TASKS_JSON}" ]]; then
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
  },
  {
    "task_id": "mab_017",
    "category": "cohort_construction",
    "difficulty": "medium",
    "instruction": "Build a cohort for type 2 diabetes with HbA1c above 8.0 in the last 90 days.",
    "expected_answer": "Patients meeting diabetes and HbA1c criteria",
    "required_actions": [],
    "split": "std",
    "task_type": "query",
    "backend_profile": "fhir"
  }
]
JSON
  echo "[setup] wrote sample benchmark asset: ${TASKS_JSON}"
else
  echo "[setup] found existing asset: ${TASKS_JSON}"
fi

"${ROOT_DIR}/.venv/bin/python" - "${TASKS_JSON}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
raw = json.loads(path.read_text(encoding="utf-8"))
if not isinstance(raw, list):
    raise SystemExit("tasks.json must contain a top-level list")
required = {"task_id", "category", "difficulty", "instruction", "split", "task_type"}
for i, row in enumerate(raw):
    if not isinstance(row, dict):
        raise SystemExit(f"task index {i} is not an object")
    missing = sorted(required - row.keys())
    if missing:
        raise SystemExit(f"task index {i} missing required keys: {', '.join(missing)}")
print(f"validated {len(raw)} task records")
PY

(
  cd "${ASSET_DIR}"
  sha256sum "tasks.json" > "${CHECKSUMS_FILE}"
)

echo "[setup] wrote checksums: ${CHECKSUMS_FILE}"
echo "[setup] medagentbench assets ready"
