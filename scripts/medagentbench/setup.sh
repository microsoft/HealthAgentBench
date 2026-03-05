#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="${ROOT_DIR}/data/medagentbench"
TEST_DATA_JSON="${DATA_DIR}/test_data_v2.json"
FUNCS_JSON="${DATA_DIR}/funcs_v1.json"
REFSOL_PY="${DATA_DIR}/refsol.py"
CHECKSUMS_FILE="${DATA_DIR}/SHA256SUMS"

TEST_DATA_URL="https://raw.githubusercontent.com/stanfordmlgroup/MedAgentBench/main/data/medagentbench/test_data_v2.json"
FUNCS_URL="https://raw.githubusercontent.com/stanfordmlgroup/MedAgentBench/main/data/medagentbench/funcs_v1.json"
REFSOL_URL="https://stanfordmedicine.box.com/s/fizv0unyjgkb1r3a83rfn5p3dc673uho"
FHIR_BASE_URL="${FHIR_BASE_URL:-http://localhost:8080/fhir}"
BACKFILL_SOL="${BACKFILL_SOL:-1}"

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

download_refsol() {
  local out_file="$1"
  local tmp_file="${out_file}.tmp"
  local candidate_urls=(
    "${REFSOL_URL}"
    "${REFSOL_URL}?download=1"
  )

  for url in "${candidate_urls[@]}"; do
    if curl -fsSL "${url}" -o "${tmp_file}"; then
      if grep -q "def task1" "${tmp_file}" && grep -q "def task10" "${tmp_file}"; then
        mv "${tmp_file}" "${out_file}"
        echo "[setup] downloaded ${out_file} from ${url}"
        return 0
      fi
    fi
  done

  rm -f "${tmp_file}"
  return 1
}

if [[ ! -f "${REFSOL_PY}" ]]; then
  echo "[setup] downloading ${REFSOL_PY}"
  if ! download_refsol "${REFSOL_PY}"; then
    echo "[setup] failed to download a valid refsol.py from Box URL" >&2
    exit 1
  fi
else
  echo "[setup] found existing file: ${REFSOL_PY}"
fi

"${ROOT_DIR}/.venv/bin/python" - "${TEST_DATA_JSON}" "${FUNCS_JSON}" "${FHIR_BASE_URL}" "${BACKFILL_SOL}" <<'PY'
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

test_data_path = Path(sys.argv[1])
funcs_path = Path(sys.argv[2])
fhir_base_url = sys.argv[3].rstrip("/")
backfill_sol = sys.argv[4] not in {"0", "false", "False", "FALSE", ""}

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

test_data_path.write_text(
    json.dumps(test_data, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
funcs_path.write_text(
    json.dumps(funcs_data, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def get_patient_birthdate(mrn: str) -> str | None:
    url = (
        f"{fhir_base_url}/Patient?identifier="
        f"{urllib.parse.quote(mrn)}&_format=json"
    )
    bundle = get_json(url)
    entries = bundle.get("entry", [])
    if not entries:
        return None
    return entries[0].get("resource", {}).get("birthDate")

def get_observations(mrn: str, code: str) -> list[dict]:
    url = (
        f"{fhir_base_url}/Observation?patient={urllib.parse.quote(mrn)}"
        f"&code={urllib.parse.quote(code)}&_count=5000&_format=json"
    )
    bundle = get_json(url)
    return [entry.get("resource", {}) for entry in bundle.get("entry", [])]

def parse_effective_dt(resource: dict) -> datetime | None:
    value = resource.get("effectiveDateTime")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None

def parse_quantity(resource: dict) -> float | None:
    value = resource.get("valueQuantity", {}).get("value")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def calc_task2(mrn: str) -> list[float | int]:
    dob_str = get_patient_birthdate(mrn)
    if not dob_str:
        return [-1]
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    today = datetime(2023, 11, 13)
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return [age]

def calc_latest_within_24h(mrn: str, code: str) -> list[float | int]:
    obs = get_observations(mrn, code)
    cutoff = datetime.fromisoformat("2023-11-13T10:15:00+00:00")
    latest_time = None
    latest_val = None
    for resource in obs:
        effective = parse_effective_dt(resource)
        value = parse_quantity(resource)
        if effective is None or value is None:
            continue
        if effective >= (cutoff - timedelta(hours=24)):
            if latest_time is None or effective > latest_time:
                latest_time = effective
                latest_val = value
    return [latest_val if latest_val is not None else -1]

def calc_avg_within_24h(mrn: str, code: str) -> list[float | int]:
    obs = get_observations(mrn, code)
    cutoff = datetime.fromisoformat("2023-11-13T10:15:00+00:00")
    values: list[float] = []
    for resource in obs:
        effective = parse_effective_dt(resource)
        value = parse_quantity(resource)
        if effective is None or value is None:
            continue
        if effective >= (cutoff - timedelta(hours=24)):
            values.append(value)
    if not values:
        return [-1]
    return [sum(values) / len(values)]

def calc_latest(mrn: str, code: str) -> list[float | int]:
    obs = get_observations(mrn, code)
    latest_time = None
    latest_val = None
    for resource in obs:
        effective = parse_effective_dt(resource)
        value = parse_quantity(resource)
        if effective is None or value is None:
            continue
        if latest_time is None or effective > latest_time:
            latest_time = effective
            latest_val = value
    return [latest_val if latest_val is not None else -1]

def calc_latest_a1c(mrn: str) -> list[float | int | str]:
    obs = get_observations(mrn, "A1C")
    latest_time = None
    latest_val = None
    for resource in obs:
        effective = parse_effective_dt(resource)
        value = parse_quantity(resource)
        if effective is None or value is None:
            continue
        if latest_time is None or effective > latest_time:
            latest_time = effective
            latest_val = value
    if latest_time is None or latest_val is None:
        return [-1]
    return [latest_val, latest_time.isoformat()]

if backfill_sol:
    try:
        get_json(f"{fhir_base_url}/metadata")
        reachable = True
    except (urllib.error.URLError, TimeoutError):
        reachable = False

    if not reachable:
        print(
            "warning: FHIR endpoint not reachable; skipping sol backfill "
            f"(set FHIR_BASE_URL or start server). endpoint={fhir_base_url}"
        )
    else:
        updated = 0
        by_group: Counter[str] = Counter()
        for row in test_data:
            task_id = row.get("id", "")
            mrn = row.get("eval_MRN")
            if not task_id or not mrn:
                continue
            group = task_id.split("_", 1)[0]
            value = None
            if group == "task2":
                value = calc_task2(mrn)
            elif group == "task4":
                value = calc_latest_within_24h(mrn, "MG")
            elif group == "task5":
                value = calc_latest_within_24h(mrn, "MG")
            elif group == "task6":
                value = calc_avg_within_24h(mrn, "GLU")
            elif group == "task7":
                value = calc_latest(mrn, "GLU")
            elif group == "task9":
                value = calc_latest(mrn, "K")
            elif group == "task10":
                value = calc_latest_a1c(mrn)
            if value is not None:
                row["sol"] = value
                updated += 1
                by_group[group] += 1

        test_data_path.write_text(
            json.dumps(test_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"updated sols: {updated}")
        print(f"updated groups: {dict(sorted(by_group.items()))}")

print(f"validated task rows: {len(test_data)}")
print(f"validated function schemas: {len(funcs_data)}")
PY

(
  cd "${DATA_DIR}"
  sha256sum "test_data_v2.json" "funcs_v1.json" "refsol.py" > "${CHECKSUMS_FILE}"
)

echo "[setup] wrote checksums: ${CHECKSUMS_FILE}"
echo "[setup] medagentbench assets ready"
