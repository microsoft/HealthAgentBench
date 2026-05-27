from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

UPSTREAM_REPO = "https://github.com/Medical-Event-Data-Standard/MIMIC_IV_MEDS.git"
UPSTREAM_TAG = "0.0.7"
UPSTREAM_COMMIT = "9699e0865b050325459b11f3c4e226a9dbe5b496"
UV_VERSION = "0.9.26"
PYTHON_BASE = "3.11-slim"
DEMO_BASE_URL = "https://physionet.org/files/mimic-iv-demo/2.2"
COMMON_BASE_URL = "https://raw.githubusercontent.com/MIT-LCP/mimic-code/v2.4.0/mimic-iv/concepts/concept_map"
OUTPUT_ROOT_DEFAULT = Path("tasks/mimic_iv_meds")
GOLD_SUMMARY_ASSET = Path("scripts/mimic_iv_meds/assets/gold_demo_summary.json")
REFERENCE_CUSTOM_CONFIG_ASSET = Path(
    "scripts/mimic_iv_meds/assets/reference_custom_event_configs.yaml"
)
DEFAULT_EVENT_CONFIG_REL_PATH = "src/MIMIC_IV_MEDS/configs/event_configs.yaml"
CUSTOM_EVENT_CONFIG_REL_PATH = "src/MIMIC_IV_MEDS/configs/custom_event_configs.yaml"

DEMO_FILES = [
    "LICENSE.txt",
    "README.txt",
    "SHA256SUMS.txt",
    "d_labitems_to_loinc.csv",
    "demo_subject_id.csv",
    "hosp/admissions.csv.gz",
    "hosp/d_hcpcs.csv.gz",
    "hosp/d_icd_diagnoses.csv.gz",
    "hosp/d_icd_procedures.csv.gz",
    "hosp/d_labitems.csv.gz",
    "hosp/diagnoses_icd.csv.gz",
    "hosp/drgcodes.csv.gz",
    "hosp/emar.csv.gz",
    "hosp/emar_detail.csv.gz",
    "hosp/hcpcsevents.csv.gz",
    "hosp/labevents.csv.gz",
    "hosp/microbiologyevents.csv.gz",
    "hosp/omr.csv.gz",
    "hosp/patients.csv.gz",
    "hosp/pharmacy.csv.gz",
    "hosp/poe.csv.gz",
    "hosp/poe_detail.csv.gz",
    "hosp/prescriptions.csv.gz",
    "hosp/procedures_icd.csv.gz",
    "hosp/provider.csv.gz",
    "hosp/services.csv.gz",
    "hosp/transfers.csv.gz",
    "icu/caregiver.csv.gz",
    "icu/chartevents.csv.gz",
    "icu/d_items.csv.gz",
    "icu/datetimeevents.csv.gz",
    "icu/icustays.csv.gz",
    "icu/ingredientevents.csv.gz",
    "icu/inputevents.csv.gz",
    "icu/outputevents.csv.gz",
    "icu/procedureevents.csv.gz",
    "inputevents_to_rxnorm.csv",
    "lab_itemid_to_loinc.csv",
    "meas_chartevents_main.csv",
    "meas_chartevents_value.csv",
    "numerics-summary.csv",
    "outputevents_to_loinc.csv",
    "proc_datetimeevents.csv",
    "proc_itemid.csv",
    "waveforms-summary.csv",
]


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_instruction() -> str:
    return f"""# MIMIC-IV MEDS Extraction ETL

Use the codebase at `/workspace/MIMIC_IV_MEDS` to run its ETL pipeline on the demo input at `/workspace/staged_demo/raw_input`.

Inspect the repository, use `uv` from the repo root to install and run the pipeline, and write the final MEDS cohort under `/workspace/output/MEDS_cohort`.

Inspect the default extraction config at `/workspace/MIMIC_IV_MEDS/{DEFAULT_EVENT_CONFIG_REL_PATH}`. Create a new config at `/workspace/MIMIC_IV_MEDS/{CUSTOM_EVENT_CONFIG_REL_PATH}` by copying that default config and editing the copy.

Leave the default config file unchanged, and keep the repo's default config wiring pointed at that default config. Do not solve this by changing the package so your custom config becomes the new default.

Run the ETL with your new config for this run only. If you need to make a small code change so the ETL can accept an explicit non-default config path at runtime, that is allowed.

The new config must produce a customized extraction so that the final MEDS cohort:

- no longer stores `insurance`, `language`, `marital_status`, or `race` as fields on the hospital admission event
- records each of those four admission-time demographics as its own event at the admission timestamp using the prefixes `INSURANCE//...`, `LANGUAGE//...`, `MARITAL_STATUS//...`, and `RACE//...`
- uses `OMR//...` for outpatient OMR measurements
- uses `HOSP_LAB//...` for hospital lab events from `hosp/labevents`
- uses `ICU_CHARTEVENT//...` for ICU chart events from `icu/chartevents`

You may use `/workspace/output` for intermediate outputs.

Submission rules:

- Do not modify files under `/tests`.
- The task is complete only when the ETL run succeeds and the expected MEDS files are present.
"""


def build_workspace_readme() -> str:
    return """# MIMIC-IV MEDS Task Workspace

Available paths:

- `/workspace/MIMIC_IV_MEDS`: ETL codebase to inspect and run
- `/workspace/staged_demo/raw_input`: staged MIMIC-IV demo input
- `/workspace/output`: writable output directory
- `/workspace/scripts/stage_demo_data.py`: helper used during image build to stage the demo input
"""


def build_task_toml() -> str:
    return """version = "1.0"

[metadata]
benchmark = "mimic_iv_meds"
mode = "etl-task"
output_dir = "/workspace/output/MEDS_cohort"
repo_dir = "/workspace/MIMIC_IV_MEDS"

[verifier]
timeout_sec = 900.0

[agent]
timeout_sec = 7200.0

[environment]
build_timeout_sec = 3600.0
allow_internet = true
cpus = 4
memory_mb = 8192
storage_mb = 20480
gpus = 0
mcp_servers = []

[verifier.env]

[solution.env]
"""


def build_verify_test_sh() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /logs/artifacts

: "${VERIFIER_ERROR_ANALYSIS_FILE:=/logs/artifacts/error_analysis.json}"

python /tests/verify_output.py \
  --repo-dir /workspace/MIMIC_IV_MEDS \
  --output-root /workspace/output \
  --gold-summary /tests/gold_demo_summary.json \
  --reward-file /logs/verifier/reward.txt \
  --error-analysis-file "${VERIFIER_ERROR_ANALYSIS_FILE}"
"""


def build_verify_output_py() -> str:
    return r'''from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq
import yaml


DEFAULT_EVENT_CONFIG_REL_PATH = Path("DEFAULT_EVENT_CONFIG_REL_PATH_PLACEHOLDER")
CUSTOM_EVENT_CONFIG_REL_PATH = Path("CUSTOM_EVENT_CONFIG_REL_PATH_PLACEHOLDER")
INIT_PY_REL_PATH = Path("INIT_PY_REL_PATH_PLACEHOLDER")
DEFAULT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def normalize_columns(columns: list[dict]) -> list[dict]:
    return sorted(columns, key=lambda column: column["name"])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def normalize_dataset_json(payload: dict) -> dict:
    normalized = {key: value for key, value in payload.items() if key != "created_at"}
    dataset_version = normalized.get("dataset_version")
    if isinstance(dataset_version, str) and ":" in dataset_version:
        normalized["dataset_version"] = dataset_version.split(":", 1)[0]
    return normalized


def parquet_summary(path: Path) -> dict:
    table = pq.read_table(path)
    return {
        "rows": table.num_rows,
        "columns": normalize_columns([
            {"name": field.name, "type": str(field.type)} for field in table.schema
        ]),
    }


def parquet_content_sha256(path: Path, sort_by: list[str]) -> str:
    table = pq.read_table(path)
    rows = table.to_pylist()
    rows.sort(key=lambda row: tuple((row[key] is None, row[key]) for key in sort_by))
    payload = {
        "rows": table.num_rows,
        "columns": normalize_columns(
            [{"name": field.name, "type": str(field.type)} for field in table.schema]
        ),
        "records": rows,
    }
    return canonical_json_sha256(payload)


def data_code_prefix_counts(meds_root: Path, data_paths: list[str], prefixes: list[str]) -> dict[str, int]:
    counts = {prefix: 0 for prefix in prefixes}
    for rel_path in data_paths:
        codes = pq.read_table(meds_root / rel_path, columns=["code"]).column("code").to_pylist()
        for prefix in prefixes:
            counts[prefix] += sum(isinstance(code, str) and code.startswith(prefix) for code in codes)
    return counts


def load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected top-level YAML mapping in {path}.")
    return payload


def code_parts(value: object) -> list[str] | None:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(part, str) for part in value):
        return value
    return None


def normalize_code(value: object) -> tuple[str, ...] | None:
    parts = code_parts(value)
    if parts is None:
        return None
    return tuple(parts)


def validate_default_config(repo_dir: Path, error_taxonomy: dict[str, int], failures: list[dict]) -> None:
    path = repo_dir / DEFAULT_EVENT_CONFIG_REL_PATH
    if not path.exists():
        fail(
            error_taxonomy,
            failures,
            "default_config_missing",
            f"Expected default config at {DEFAULT_EVENT_CONFIG_REL_PATH.as_posix()}.",
        )
        return

    try:
        payload = load_yaml(path)
    except Exception as exc:
        fail(
            error_taxonomy,
            failures,
            "default_config_modified",
            "Default extraction config could not be parsed.",
            error=str(exc),
        )
        return

    admissions = payload.get("hosp/admissions")
    patients = payload.get("hosp/patients")
    labevents = payload.get("hosp/labevents")
    omr = payload.get("hosp/omr", {}).get("omr") if isinstance(payload.get("hosp/omr"), dict) else None
    chartevents = (
        payload.get("icu/chartevents", {}).get("event")
        if isinstance(payload.get("icu/chartevents"), dict)
        else None
    )

    if not isinstance(admissions, dict):
        fail(
            error_taxonomy,
            failures,
            "default_config_modified",
            "Default config is missing the hosp/admissions block.",
        )
        return

    admission = admissions.get("admission")
    if not isinstance(admission, dict):
        fail(
            error_taxonomy,
            failures,
            "default_config_modified",
            "Default config is missing the admission event block.",
        )
        return

    missing_default_fields = [
        key for key in ("insurance", "language", "marital_status", "race") if admission.get(key) != key
    ]
    unexpected_custom_blocks = [
        name for name in ("admission_insurance", "admission_language", "admission_marital_status", "admission_race")
        if name in admissions
    ]
    gender_code = (
        code_parts(patients.get("gender", {}).get("code"))
        if isinstance(patients, dict) and isinstance(patients.get("gender"), dict)
        else None
    )
    labevent_code = (
        code_parts(labevents.get("lab", {}).get("code"))
        if isinstance(labevents, dict) and isinstance(labevents.get("lab"), dict)
        else None
    )
    omr_code = code_parts(omr.get("code")) if isinstance(omr, dict) else None
    chartevent_code = code_parts(chartevents.get("code")) if isinstance(chartevents, dict) else None

    if (
        missing_default_fields
        or unexpected_custom_blocks
        or gender_code != ["GENDER", "col(gender)"]
        or labevent_code != ["LAB", "col(itemid)", "col(valueuom)"]
        or omr_code != ["col(result_name)"]
        or chartevent_code is None
        or chartevent_code[:1] != ["LAB"]
    ):
        fail(
            error_taxonomy,
            failures,
            "default_config_modified",
            "Default extraction config was modified; it must remain unchanged.",
            missing_default_fields=missing_default_fields,
            unexpected_custom_blocks=unexpected_custom_blocks,
            gender_code=gender_code,
            labevent_code=labevent_code,
            omr_code=omr_code,
            chartevent_code=chartevent_code,
        )


def validate_default_config_wiring(
    repo_dir: Path,
    error_taxonomy: dict[str, int],
    failures: list[dict],
) -> None:
    path = repo_dir / INIT_PY_REL_PATH
    if not path.exists():
        fail(
            error_taxonomy,
            failures,
            "default_config_wiring_modified",
            f"Expected package init file at {INIT_PY_REL_PATH.as_posix()}.",
        )
        return

    text = path.read_text(encoding="utf-8")
    if 'joinpath("configs/event_configs.yaml")' not in text:
        fail(
            error_taxonomy,
            failures,
            "default_config_wiring_modified",
            "Default config wiring was modified; keep the packaged default pointed at event_configs.yaml.",
        )


def validate_custom_config(
    repo_dir: Path,
    error_taxonomy: dict[str, int],
    failures: list[dict],
) -> None:
    path = repo_dir / CUSTOM_EVENT_CONFIG_REL_PATH
    if not path.exists():
        fail(
            error_taxonomy,
            failures,
            "missing_custom_config",
            f"Expected custom config at {CUSTOM_EVENT_CONFIG_REL_PATH.as_posix()}.",
        )
        return

    try:
        payload = load_yaml(path)
    except Exception as exc:
        fail(
            error_taxonomy,
            failures,
            "custom_config_invalid",
            "Custom extraction config could not be parsed.",
            error=str(exc),
        )
        return

    admissions = payload.get("hosp/admissions")
    if not isinstance(admissions, dict):
        fail(
            error_taxonomy,
            failures,
            "custom_config_invalid",
            "Custom extraction config is missing the hosp/admissions block.",
        )
        return

    admission = admissions.get("admission")
    if not isinstance(admission, dict):
        fail(
            error_taxonomy,
            failures,
            "custom_config_invalid",
            "Custom extraction config is missing the admission event block.",
        )
        return

    lingering_fields = [
        key for key in ("insurance", "language", "marital_status", "race") if key in admission
    ]
    if lingering_fields:
        fail(
            error_taxonomy,
            failures,
            "custom_config_behavior_missing",
            "Admission event still stores demographics that should be split into separate events.",
            lingering_fields=lingering_fields,
        )

    expected_demographic_codes = {
        ("INSURANCE", "col(insurance)"),
        ("LANGUAGE", "col(language)"),
        ("MARITAL_STATUS", "col(marital_status)"),
        ("RACE", "col(race)"),
    }
    found_demographic_codes: set[tuple[str, ...]] = set()
    wrong_demographic_timing: list[dict[str, object]] = []

    for event_name, event_cfg in admissions.items():
        if not isinstance(event_cfg, dict):
            continue
        code = normalize_code(event_cfg.get("code"))
        if code in expected_demographic_codes:
            found_demographic_codes.add(code)
            if event_cfg.get("time") != "col(admittime)":
                wrong_demographic_timing.append(
                    {
                        "event_name": event_name,
                        "code": list(code),
                        "actual_time": event_cfg.get("time"),
                    }
                )

    if found_demographic_codes != expected_demographic_codes:
        fail(
            error_taxonomy,
            failures,
            "custom_config_behavior_missing",
            "Custom extraction config is missing one or more required admission demographic events.",
            missing_event_codes=[list(code) for code in sorted(expected_demographic_codes - found_demographic_codes)],
        )

    if wrong_demographic_timing:
        fail(
            error_taxonomy,
            failures,
            "custom_config_behavior_missing",
            "Admission demographic events must use the admission timestamp.",
            wrong_demographic_timing=wrong_demographic_timing,
        )

    omr = payload.get("hosp/omr", {}).get("omr") if isinstance(payload.get("hosp/omr"), dict) else None
    labevents = payload.get("hosp/labevents", {}).get("lab") if isinstance(payload.get("hosp/labevents"), dict) else None
    chartevents = (
        payload.get("icu/chartevents", {}).get("event")
        if isinstance(payload.get("icu/chartevents"), dict)
        else None
    )

    code_failures: list[dict[str, object]] = []
    for label, event_cfg, expected_prefix in (
        ("hosp/omr.omr", omr, "OMR"),
        ("hosp/labevents.lab", labevents, "HOSP_LAB"),
        ("icu/chartevents.event", chartevents, "ICU_CHARTEVENT"),
    ):
        code = normalize_code(event_cfg.get("code")) if isinstance(event_cfg, dict) else None
        if code is None or not code or code[0] != expected_prefix:
            code_failures.append(
                {
                    "event": label,
                    "expected_prefix": expected_prefix,
                    "actual_code": list(code) if code is not None else None,
                }
            )

    if code_failures:
        fail(
            error_taxonomy,
            failures,
            "custom_config_behavior_missing",
            "Custom extraction config is missing one or more required code prefixes.",
            code_failures=code_failures,
        )


def fail(error_taxonomy: dict[str, int], failures: list[dict], kind: str, message: str, **extra) -> None:
    error_taxonomy[kind] = error_taxonomy.get(kind, 0) + 1
    item = {"kind": kind, "message": message}
    item.update(extra)
    failures.append(item)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--gold-summary", required=True, type=Path)
    parser.add_argument("--reward-file", required=True, type=Path)
    parser.add_argument("--error-analysis-file", required=True, type=Path)
    args = parser.parse_args()

    gold = json.loads(args.gold_summary.read_text(encoding="utf-8"))
    failures: list[dict] = []
    error_taxonomy: dict[str, int] = {}

    repo_dir = args.repo_dir
    output_root = args.output_root
    meds_root = output_root / "MEDS_cohort"
    metadata_dir = meds_root / "metadata"
    data_dir = meds_root / "data"

    validate_default_config(repo_dir, error_taxonomy, failures)
    validate_default_config_wiring(repo_dir, error_taxonomy, failures)
    validate_custom_config(repo_dir, error_taxonomy, failures)

    if not meds_root.exists():
        fail(error_taxonomy, failures, "missing_output", "Expected MEDS_cohort output directory.")
    else:
        for name in gold["required_metadata_files"]:
            if not (metadata_dir / name).exists():
                fail(error_taxonomy, failures, "missing_output", f"Missing required metadata file: {name}")

        data_paths = sorted(path.relative_to(meds_root).as_posix() for path in data_dir.rglob("*.parquet")) if data_dir.exists() else []
        if not data_paths:
            fail(error_taxonomy, failures, "missing_output", "No parquet files found under MEDS_cohort/data.")

        expected_paths = [item["relative_path"] for item in gold["data_files"]]
        if data_paths != expected_paths:
            fail(
                error_taxonomy,
                failures,
                "data_file_mismatch",
                "Generated data parquet set does not match the reference summary.",
                expected=expected_paths,
                actual=data_paths,
            )

        if all((metadata_dir / name).exists() for name in gold["required_metadata_files"]):
            expected_prefix_counts = gold["semantic_expectations"]["required_data_code_prefix_counts"]
            actual_prefix_counts = data_code_prefix_counts(
                meds_root,
                data_paths,
                list(expected_prefix_counts),
            )
            missing_prefixes = {
                prefix: {
                    "expected_at_least": 1,
                    "actual": actual_prefix_counts[prefix],
                }
                for prefix, expected_count in expected_prefix_counts.items()
                if expected_count > 0 and actual_prefix_counts[prefix] == 0
            }
            if missing_prefixes:
                fail(
                    error_taxonomy,
                    failures,
                    "custom_config_behavior_missing",
                    "Output is missing code families required by the customized extraction config.",
                    missing_prefixes=missing_prefixes,
                    actual_prefix_counts=actual_prefix_counts,
                )

        if not failures:
            actual_dataset = normalize_dataset_json(
                json.loads((metadata_dir / "dataset.json").read_text(encoding="utf-8"))
            )
            expected_dataset = gold["metadata"]["dataset.json"]["normalized_json"]
            if actual_dataset != expected_dataset:
                fail(
                    error_taxonomy,
                    failures,
                    "dataset_json_mismatch",
                    "Normalized dataset.json content did not match.",
                    expected=expected_dataset,
                    actual=actual_dataset,
                )

        if not failures:
            for name in ("codes.parquet", "subject_splits.parquet"):
                actual = parquet_summary(metadata_dir / name)
                expected = {
                    "rows": gold["metadata"][name]["rows"],
                    "columns": normalize_columns(gold["metadata"][name]["columns"]),
                }
                if actual != expected:
                    fail(
                        error_taxonomy,
                        failures,
                        "metadata_mismatch",
                        f"Metadata parquet summary mismatch for {name}.",
                        expected=expected,
                        actual=actual,
                    )

        if not failures:
            for name in ("codes.parquet", "subject_splits.parquet"):
                actual_hash = parquet_content_sha256(
                    metadata_dir / name,
                    gold["metadata"][name]["sort_by"],
                )
                expected_hash = gold["metadata"][name]["content_sha256"]
                if actual_hash != expected_hash:
                    fail(
                        error_taxonomy,
                        failures,
                        "metadata_content_mismatch",
                        f"Normalized parquet content mismatch for {name}.",
                        expected=expected_hash,
                        actual=actual_hash,
                    )

        if not failures:
            expected_by_path = {item["relative_path"]: item for item in gold["data_files"]}
            for rel_path in data_paths:
                table = pq.read_table(meds_root / rel_path)
                actual_rows = table.num_rows
                expected_rows = expected_by_path[rel_path]["rows"]
                if actual_rows != expected_rows:
                    fail(
                        error_taxonomy,
                        failures,
                        "data_row_mismatch",
                        f"Row count mismatch for {rel_path}.",
                        expected=expected_rows,
                        actual=actual_rows,
                    )
                    continue

                actual_hash = parquet_content_sha256(
                    meds_root / rel_path,
                    expected_by_path[rel_path]["sort_by"],
                )
                expected_hash = expected_by_path[rel_path]["content_sha256"]
                if actual_hash != expected_hash:
                    fail(
                        error_taxonomy,
                        failures,
                        "data_hash_mismatch",
                        f"Content hash mismatch for {rel_path}.",
                        expected=expected_hash,
                        actual=actual_hash,
                    )

    reward = 1.0 if not failures else 0.0
    args.reward_file.parent.mkdir(parents=True, exist_ok=True)
    args.reward_file.write_text(f"{reward:.6f}\n", encoding="utf-8")

    args.error_analysis_file.parent.mkdir(parents=True, exist_ok=True)
    args.error_analysis_file.write_text(
        json.dumps(
            {
                "passed": not failures,
                "error_taxonomy": error_taxonomy,
                "failures": failures,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
'''.replace(
        "DEFAULT_EVENT_CONFIG_REL_PATH_PLACEHOLDER",
        DEFAULT_EVENT_CONFIG_REL_PATH,
    ).replace(
        "CUSTOM_EVENT_CONFIG_REL_PATH_PLACEHOLDER",
        CUSTOM_EVENT_CONFIG_REL_PATH,
    ).replace(
        "INIT_PY_REL_PATH_PLACEHOLDER",
        "src/MIMIC_IV_MEDS/__init__.py",
    )


def build_stage_demo_script() -> str:
    manifest = json.dumps(DEMO_FILES, indent=2)
    return f'''from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen

DEMO_BASE_URL = "{DEMO_BASE_URL}"
COMMON_BASE_URL = "{COMMON_BASE_URL}"
FILES = {manifest}
COMMON_NAMES = {{
    "d_labitems_to_loinc.csv",
    "inputevents_to_rxnorm.csv",
    "lab_itemid_to_loinc.csv",
    "meas_chartevents_main.csv",
    "meas_chartevents_value.csv",
    "numerics-summary.csv",
    "outputevents_to_loinc.csv",
    "proc_datetimeevents.csv",
    "proc_itemid.csv",
    "waveforms-summary.csv",
}}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    for rel in FILES:
        if rel in COMMON_NAMES:
            url = f"{{COMMON_BASE_URL}}/{{rel}}"
        else:
            url = f"{{DEMO_BASE_URL}}/{{rel}}"
        download(url, args.output_dir / rel)


if __name__ == "__main__":
    main()
'''


def build_runtime_patch_sitecustomize() -> str:
    return r'''from __future__ import annotations

import importlib
from pathlib import Path

PATTERN = "        lock.release()\n        lock_fp.unlink()\n"
REPLACEMENT = "        lock.release()\n        if lock_fp.exists():\n            lock_fp.unlink()\n"


def _apply_meds_lock_patch() -> None:
    try:
        import MEDS_transforms.mapreduce.utils as utils
    except Exception:
        return

    target = Path(utils.__file__)
    text = target.read_text(encoding="utf-8")
    if REPLACEMENT in text:
        return
    if PATTERN not in text:
        return

    target.write_text(text.replace(PATTERN, REPLACEMENT), encoding="utf-8")
    importlib.reload(utils)


_apply_meds_lock_patch()
'''


def build_dockerfile() -> str:
    return f'''FROM python:{PYTHON_BASE}

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv=={UV_VERSION} pyarrow==23.0.1 pyyaml==6.0.3

WORKDIR /workspace
COPY workspace/ /workspace/
ENV PYTHONPATH=/workspace/runtime_patch

RUN git clone {UPSTREAM_REPO} /workspace/MIMIC_IV_MEDS \
    && cd /workspace/MIMIC_IV_MEDS \
    && git checkout {UPSTREAM_COMMIT} \
    && test "$(git rev-parse HEAD)" = "{UPSTREAM_COMMIT}"

RUN python /workspace/scripts/stage_demo_data.py --output-dir /workspace/staged_demo/raw_input
'''


def generate_task(output_root: Path) -> None:
    ensure_clean_dir(output_root)
    workspace_dir = output_root / 'environment' / 'workspace'
    tests_dir = output_root / 'tests'

    write(output_root / 'instruction.md', build_instruction())
    write(output_root / 'task.toml', build_task_toml())
    write(workspace_dir / 'README.md', build_workspace_readme())
    write(workspace_dir / 'scripts' / 'stage_demo_data.py', build_stage_demo_script())
    write(workspace_dir / 'runtime_patch' / 'sitecustomize.py', build_runtime_patch_sitecustomize())
    write(output_root / 'environment' / 'Dockerfile', build_dockerfile())
    write(tests_dir / 'test.sh', build_verify_test_sh())
    write(tests_dir / 'verify_output.py', build_verify_output_py())

    gold_summary_text = GOLD_SUMMARY_ASSET.read_text(encoding='utf-8')
    write(tests_dir / 'gold_demo_summary.json', gold_summary_text)
    reference_config_text = REFERENCE_CUSTOM_CONFIG_ASSET.read_text(encoding='utf-8')
    write(tests_dir / 'reference_custom_event_configs.yaml', reference_config_text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-root', type=Path, default=OUTPUT_ROOT_DEFAULT)
    args = parser.parse_args()
    generate_task(args.output_root)


if __name__ == '__main__':
    main()
