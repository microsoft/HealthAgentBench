from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq


REQUIRED_METADATA_FILES = (
    "dataset.json",
    "codes.parquet",
    "subject_splits.parquet",
)
REQUIRED_CODE_PREFIXES = (
    "HOSP_LAB//",
    "ICU_CHARTEVENT//",
    "OMR//",
    "INSURANCE//",
    "LANGUAGE//",
    "MARITAL_STATUS//",
    "RACE//",
)


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


def data_code_prefix_counts(
    data_dir: Path,
    prefixes: tuple[str, ...],
) -> dict[str, int]:
    counts = {prefix: 0 for prefix in prefixes}
    for path in sorted(data_dir.rglob("*.parquet")):
        codes = pq.read_table(path, columns=["code"]).column("code").to_pylist()
        for prefix in prefixes:
            counts[prefix] += sum(
                isinstance(code, str) and code.startswith(prefix) for code in codes
            )
    return counts


def build_summary(output_root: Path) -> dict:
    meds_root = output_root / "MEDS_cohort"
    metadata_dir = meds_root / "metadata"
    data_dir = meds_root / "data"

    summary = {
        "required_metadata_files": list(REQUIRED_METADATA_FILES),
        "metadata": {},
        "data_files": [],
        "semantic_expectations": {
            "required_data_code_prefix_counts": {},
        },
    }

    dataset_json = json.loads((metadata_dir / "dataset.json").read_text(encoding="utf-8"))
    summary["metadata"]["dataset.json"] = {
        "normalized_json": normalize_dataset_json(dataset_json),
    }

    metadata_sort_keys = {
        "codes.parquet": ["code"],
        "subject_splits.parquet": ["subject_id", "split"],
    }
    for name, sort_by in metadata_sort_keys.items():
        summary["metadata"][name] = parquet_summary(metadata_dir / name) | {
            "sort_by": sort_by,
            "content_sha256": parquet_content_sha256(metadata_dir / name, sort_by),
        }

    summary["semantic_expectations"]["required_data_code_prefix_counts"] = data_code_prefix_counts(
        data_dir,
        REQUIRED_CODE_PREFIXES,
    )

    data_sort_by = ["subject_id", "time", "code"]
    for path in sorted(data_dir.rglob("*.parquet")):
        table = pq.read_table(path)
        summary["data_files"].append(
            {
                "relative_path": path.relative_to(meds_root).as_posix(),
                "rows": table.num_rows,
                "sort_by": data_sort_by,
                "content_sha256": parquet_content_sha256(path, data_sort_by),
            }
        )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--summary-out", required=True, type=Path)
    args = parser.parse_args()

    summary = build_summary(args.output_root)
    args.summary_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
