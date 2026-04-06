from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq


REQUIRED_METADATA_FILES = (
    "dataset.json",
    "codes.parquet",
    "subject_splits.parquet",
)


def parquet_summary(path: Path) -> dict:
    table = pq.read_table(path)
    return {
        "rows": table.num_rows,
        "columns": [
            {"name": field.name, "type": str(field.type)} for field in table.schema
        ],
    }


def build_summary(output_root: Path) -> dict:
    meds_root = output_root / "MEDS_cohort"
    metadata_dir = meds_root / "metadata"
    data_dir = meds_root / "data"

    summary = {
        "required_metadata_files": list(REQUIRED_METADATA_FILES),
        "metadata": {},
        "data_files": [],
    }

    dataset_json = json.loads((metadata_dir / "dataset.json").read_text(encoding="utf-8"))
    summary["metadata"]["dataset.json"] = {
        "dataset_name": dataset_json.get("dataset_name"),
        "dataset_version": dataset_json.get("dataset_version"),
        "etl_name": dataset_json.get("etl_name"),
        "etl_version": dataset_json.get("etl_version"),
    }
    for name in ("codes.parquet", "subject_splits.parquet"):
        summary["metadata"][name] = parquet_summary(metadata_dir / name)

    for path in sorted(data_dir.rglob("*.parquet")):
        table = pq.read_table(path)
        summary["data_files"].append(
            {
                "relative_path": path.relative_to(meds_root).as_posix(),
                "rows": table.num_rows,
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
