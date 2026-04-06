import json
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def _load_gold_summary() -> dict:
    return json.loads(
        Path("scripts/mimic_iv_meds/assets/gold_demo_summary.json").read_text(encoding="utf-8")
    )


def _make_repo_setup(repo_dir: Path) -> None:
    (repo_dir / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
    (repo_dir / ".venv" / "bin" / "python").write_text("", encoding="utf-8")
    (repo_dir / ".venv" / "bin" / "MEDS_extract-MIMIC_IV").write_text("", encoding="utf-8")
    (repo_dir / "uv.lock").write_text("# synthetic lock\n", encoding="utf-8")


def _arrow_type(type_name: str) -> pa.DataType:
    if type_name == "string":
        return pa.string()
    if type_name == "int64":
        return pa.int64()
    if type_name == "list<element: string>":
        return pa.list_(pa.string())
    if type_name == "large_list<element: large_string>":
        return pa.large_list(pa.large_string())
    raise ValueError(f"Unsupported test schema type: {type_name}")


def _column_values(type_name: str, rows: int):
    if type_name == "string":
        return ["x"] * rows
    if type_name == "int64":
        return list(range(rows))
    if type_name == "list<element: string>":
        return [["x"]] * rows
    if type_name == "large_list<element: large_string>":
        return [["x"]] * rows
    raise ValueError(f"Unsupported test schema type: {type_name}")


def _write_metadata_table(path: Path, summary: dict) -> None:
    arrays = []
    names = []
    for column in summary["columns"]:
        column_type = _arrow_type(column["type"])
        arrays.append(pa.array(_column_values(column["type"], summary["rows"]), type=column_type))
        names.append(column["name"])
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_arrays(arrays, names=names), path)


def _write_data_table(path: Path, rows: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"value": pa.array(list(range(rows)), type=pa.int32())}), path)


def _create_valid_output(repo_dir: Path, output_root: Path, gold: dict) -> None:
    _make_repo_setup(repo_dir)

    meds_root = output_root / "MEDS_cohort"
    metadata_dir = meds_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "dataset.json").write_text(
        json.dumps(gold["metadata"]["dataset.json"], indent=2) + "\n",
        encoding="utf-8",
    )
    for name in ("codes.parquet", "subject_splits.parquet"):
        _write_metadata_table(metadata_dir / name, gold["metadata"][name])
    for item in gold["data_files"]:
        _write_data_table(meds_root / item["relative_path"], item["rows"])


def test_generate_mimic_iv_meds_task_materializes_expected_layout(tmp_path: Path):
    output_root = tmp_path / "tasks" / "mimic_iv_meds"

    subprocess.run(
        [
            ".venv/bin/python",
            "scripts/mimic_iv_meds/generate_harbor_task.py",
            "--output-root",
            str(output_root),
        ],
        check=True,
    )

    assert (output_root / "instruction.md").exists()
    assert (output_root / "task.toml").exists()
    assert (output_root / "environment" / "Dockerfile").exists()
    assert (output_root / "environment" / "workspace" / "README.md").exists()
    assert (output_root / "environment" / "workspace" / "scripts" / "stage_demo_data.py").exists()
    assert (
        output_root / "environment" / "workspace" / "scripts" / "patch_meds_transforms_lock.py"
    ).exists()
    assert (output_root / "tests" / "verify_output.py").exists()
    assert (output_root / "tests" / "gold_demo_summary.json").exists()

    instruction = (output_root / "instruction.md").read_text(encoding="utf-8")
    dockerfile = (output_root / "environment" / "Dockerfile").read_text(encoding="utf-8")
    verifier = (output_root / "tests" / "verify_output.py").read_text(encoding="utf-8")
    task_toml = (output_root / "task.toml").read_text(encoding="utf-8")
    workspace_readme = (output_root / "environment" / "workspace" / "README.md").read_text(
        encoding="utf-8"
    )

    assert "uv sync" in instruction
    assert "patch_meds_transforms_lock.py" in instruction
    assert "root_output_dir=/workspace/output" in instruction
    assert "MEDS_cohort_dir=/workspace/output/MEDS_cohort" in instruction
    assert "git checkout 9699e0865b050325459b11f3c4e226a9dbe5b496" in dockerfile
    assert "python /workspace/scripts/stage_demo_data.py" in dockerfile
    assert "missing_uv_setup" in verifier
    assert "data_row_mismatch" in verifier
    assert 'benchmark = "mimic_iv_meds"' in task_toml
    assert "allow_internet = true" in task_toml
    assert "uv sync" in workspace_readme


def test_mimic_iv_meds_verifier_requires_uv_setup_and_accepts_matching_output(tmp_path: Path):
    gold = _load_gold_summary()
    repo_dir = tmp_path / "workspace" / "MIMIC_IV_MEDS"
    output_root = tmp_path / "workspace" / "output"
    reward_file = tmp_path / "logs" / "reward.txt"
    error_file = tmp_path / "logs" / "error_analysis.json"

    _create_valid_output(repo_dir, output_root, gold)

    subprocess.run(
        [
            ".venv/bin/python",
            "tasks/mimic_iv_meds/tests/verify_output.py",
            "--repo-dir",
            str(repo_dir),
            "--output-root",
            str(output_root),
            "--gold-summary",
            "tasks/mimic_iv_meds/tests/gold_demo_summary.json",
            "--reward-file",
            str(reward_file),
            "--error-analysis-file",
            str(error_file),
        ],
        check=True,
    )

    assert reward_file.read_text(encoding="utf-8").strip() == "1.000000"
    passed_payload = json.loads(error_file.read_text(encoding="utf-8"))
    assert passed_payload["passed"] is True
    assert passed_payload["failures"] == []

    (repo_dir / ".venv").rename(repo_dir / ".venv_hidden")
    reward_file.unlink()
    error_file.unlink()

    subprocess.run(
        [
            ".venv/bin/python",
            "tasks/mimic_iv_meds/tests/verify_output.py",
            "--repo-dir",
            str(repo_dir),
            "--output-root",
            str(output_root),
            "--gold-summary",
            "tasks/mimic_iv_meds/tests/gold_demo_summary.json",
            "--reward-file",
            str(reward_file),
            "--error-analysis-file",
            str(error_file),
        ],
        check=True,
    )

    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    failed_payload = json.loads(error_file.read_text(encoding="utf-8"))
    assert failed_payload["passed"] is False
    assert failed_payload["error_taxonomy"]["missing_uv_setup"] >= 1
