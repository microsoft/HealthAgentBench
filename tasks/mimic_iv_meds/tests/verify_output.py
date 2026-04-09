from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq
import yaml


DEFAULT_EVENT_CONFIG_REL_PATH = Path("src/MIMIC_IV_MEDS/configs/event_configs.yaml")
CUSTOM_EVENT_CONFIG_REL_PATH = Path("src/MIMIC_IV_MEDS/configs/custom_event_configs.yaml")
REFERENCE_CONFIG_PATH = Path("/tests/reference_custom_event_configs.yaml")
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
    rows.sort(key=lambda row: tuple(row[key] for key in sort_by))
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


def validate_custom_config(
    repo_dir: Path,
    reference_config_path: Path,
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

    try:
        reference_payload = load_yaml(reference_config_path)
    except Exception as exc:
        fail(
            error_taxonomy,
            failures,
            "reference_config_invalid",
            "Reference extraction config could not be parsed.",
            error=str(exc),
        )
        return

    if payload != reference_payload:
        fail(
            error_taxonomy,
            failures,
            "custom_config_mismatch",
            "Custom extraction config did not match the expected customized extraction.",
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
    parser.add_argument("--reference-config", type=Path, default=REFERENCE_CONFIG_PATH)
    parser.add_argument("--gold-summary", required=True, type=Path)
    parser.add_argument("--reward-file", required=True, type=Path)
    parser.add_argument("--error-analysis-file", required=True, type=Path)
    args = parser.parse_args()

    gold = json.loads(args.gold_summary.read_text(encoding="utf-8"))
    failures: list[dict] = []
    error_taxonomy: dict[str, int] = {}

    repo_dir = args.repo_dir
    venv_dir = repo_dir / ".venv"
    output_root = args.output_root
    meds_root = output_root / "MEDS_cohort"
    metadata_dir = meds_root / "metadata"
    data_dir = meds_root / "data"

    # uv setup checks
    if not (repo_dir / "uv.lock").exists():
        fail(error_taxonomy, failures, "missing_uv_setup", "Expected repo-local uv.lock after setup.")
    if not venv_dir.exists():
        fail(error_taxonomy, failures, "missing_uv_setup", "Expected repo-local .venv after uv setup.")
    if not (venv_dir / "bin" / "python").exists():
        fail(error_taxonomy, failures, "missing_uv_setup", "Expected .venv/bin/python after uv setup.")
    if not (venv_dir / "bin" / "MEDS_extract-MIMIC_IV").exists():
        fail(error_taxonomy, failures, "missing_uv_setup", "Expected MEDS_extract-MIMIC_IV in the repo-local uv environment.")

    validate_default_config(repo_dir, error_taxonomy, failures)
    validate_custom_config(repo_dir, args.reference_config, error_taxonomy, failures)

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

                actual_hash = file_sha256(meds_root / rel_path)
                expected_hash = expected_by_path[rel_path]["sha256"]
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
