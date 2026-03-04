#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="${ROOT_DIR}/data/medagentbench"
TEST_DATA_JSON="${DATA_DIR}/test_data_v2.json"
FUNCS_JSON="${DATA_DIR}/funcs_v1.json"
CHECKSUMS_FILE="${DATA_DIR}/SHA256SUMS"

TEST_DATA_URL="https://raw.githubusercontent.com/stanfordmlgroup/MedAgentBench/main/data/medagentbench/test_data_v2.json"
FUNCS_URL="https://raw.githubusercontent.com/stanfordmlgroup/MedAgentBench/main/data/medagentbench/funcs_v1.json"

mkdir -p "${DATA_DIR}"

if [[ ! -f "${TEST_DATA_JSON}" ]]; then
  echo "[setup] downloading ${TEST_DATA_JSON}"
  curl -fsSL "${TEST_DATA_URL}" -o "${TEST_DATA_JSON}"
else
  echo "[setup] found existing file: ${TEST_DATA_JSON}"
fi

if [[ ! -f "${FUNCS_JSON}" ]]; then
  echo "[setup] downloading ${FUNCS_JSON}"
  curl -fsSL "${FUNCS_URL}" -o "${FUNCS_JSON}"
else
  echo "[setup] found existing file: ${FUNCS_JSON}"
fi

"${ROOT_DIR}/.venv/bin/python" - "${TEST_DATA_JSON}" "${FUNCS_JSON}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

test_data_path = Path(sys.argv[1])
funcs_path = Path(sys.argv[2])

test_data = json.loads(test_data_path.read_text(encoding="utf-8"))
if not isinstance(test_data, list) or not test_data:
    raise SystemExit("test_data_v2.json must contain a non-empty list")
required_task_keys = {"id", "instruction", "context"}
for i, row in enumerate(test_data):
    if not isinstance(row, dict):
        raise SystemExit(f"test_data row {i} is not an object")
    missing = sorted(required_task_keys - row.keys())
    if missing:
        raise SystemExit(f"test_data row {i} missing keys: {', '.join(missing)}")

funcs_data = json.loads(funcs_path.read_text(encoding="utf-8"))
if not isinstance(funcs_data, list) or not funcs_data:
    raise SystemExit("funcs_v1.json must contain a non-empty list")
required_func_keys = {"name", "description", "parameters"}
for i, row in enumerate(funcs_data):
    if not isinstance(row, dict):
        raise SystemExit(f"funcs row {i} is not an object")
    missing = sorted(required_func_keys - row.keys())
    if missing:
        raise SystemExit(f"funcs row {i} missing keys: {', '.join(missing)}")

print(f"validated task rows: {len(test_data)}")
print(f"validated function schemas: {len(funcs_data)}")
PY

(
  cd "${DATA_DIR}"
  sha256sum "test_data_v2.json" "funcs_v1.json" > "${CHECKSUMS_FILE}"
)

echo "[setup] wrote checksums: ${CHECKSUMS_FILE}"
echo "[setup] medagentbench assets ready"
