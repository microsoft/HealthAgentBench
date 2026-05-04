"""Offline tests for scripts/mimic_iv_dq/stage_data.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "mimic_iv_dq"))

from stage_data import _verify_against, main  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "mimic_iv_dq" / "raw"


@pytest.fixture
def task_config_path(tmp_path: Path) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(
        "id: task_001\n"
        "seed: 0\n"
        "in_scope_patient_count: 10\n"
        "tables: [labevents]\n"
        "injectors:\n"
        "  - {family: impossible_value, count: 12}\n"
    )
    return p


def test_stage_data_e2e_offline(tmp_path: Path, task_config_path: Path) -> None:
    """End-to-end: read fixture, corrupt, write CSVs + DuckDB + labels."""
    output_dir = tmp_path / "data"
    labels_path = tmp_path / "labels.csv"

    main(
        [
            "--config",
            str(task_config_path),
            "--output-dir",
            str(output_dir),
            "--input-dir",
            str(RAW_FIXTURE),
            "--labels-output",
            str(labels_path),
        ]
    )

    # All eight tables present.
    csv_dir = output_dir / "csv"
    expected_tables = [
        "patients",
        "admissions",
        "labevents",
        "prescriptions",
        "d_labitems",
        "icustays",
        "chartevents",
        "d_items",
    ]
    for t in expected_tables:
        assert (csv_dir / f"{t}.csv.gz").exists(), f"{t} missing"

    # DuckDB built and queryable.
    duckdb_path = output_dir / "ehr.duckdb"
    assert duckdb_path.exists()
    import duckdb  # local import: keeps test failures legible if missing

    conn = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        rows = conn.execute("SELECT count(*) FROM labevents").fetchone()
        assert rows[0] > 0
    finally:
        conn.close()

    # Labels CSV present, with expected schema.
    labels = pd.read_csv(labels_path, dtype=str, keep_default_na=False)
    assert not labels.empty
    assert set(labels.columns) >= {
        "table",
        "row_id",
        "error_family",
        "error_subtype",
        "field",
        "original_value",
        "corrupted_value",
        "severity",
        "cluster_id",
    }
    assert (labels["error_family"] == "impossible_value").all()


def test_verify_against_passes_for_self_consistent_run(
    tmp_path: Path, task_config_path: Path
) -> None:
    """Verifier passes when labels.csv matches the corrupted CSVs."""
    output_dir = tmp_path / "data"
    labels_path = tmp_path / "labels.csv"

    main(
        [
            "--config",
            str(task_config_path),
            "--output-dir",
            str(output_dir),
            "--input-dir",
            str(RAW_FIXTURE),
            "--labels-output",
            str(labels_path),
        ]
    )

    # Should not raise.
    _verify_against(labels_path, output_dir / "csv")


def test_verify_against_fails_when_csv_diverges(
    tmp_path: Path, task_config_path: Path
) -> None:
    output_dir = tmp_path / "data"
    labels_path = tmp_path / "labels.csv"
    main(
        [
            "--config",
            str(task_config_path),
            "--output-dir",
            str(output_dir),
            "--input-dir",
            str(RAW_FIXTURE),
            "--labels-output",
            str(labels_path),
        ]
    )

    # Mutate the labevents CSV to scramble the labeled corruption.
    csv_path = output_dir / "csv" / "labevents.csv.gz"
    df = pd.read_csv(csv_path, compression="gzip", low_memory=False)
    df["valuenum"] = 0
    df.to_csv(csv_path, index=False, compression="gzip")

    with pytest.raises(SystemExit, match="Build-time label verification failed"):
        _verify_against(labels_path, output_dir / "csv")


def test_no_duckdb_flag(tmp_path: Path, task_config_path: Path) -> None:
    output_dir = tmp_path / "data"
    main(
        [
            "--config",
            str(task_config_path),
            "--output-dir",
            str(output_dir),
            "--input-dir",
            str(RAW_FIXTURE),
            "--no-duckdb",
        ]
    )
    assert not (output_dir / "ehr.duckdb").exists()
    assert (output_dir / "csv" / "labevents.csv.gz").exists()
