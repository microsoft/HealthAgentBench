import json
import subprocess
import textwrap
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


DEFAULT_EVENT_CONFIG_TEXT = textwrap.dedent(
    """\
    subject_id_col: subject_id
    hosp/admissions:
      admission:
        code:
          - HOSPITAL_ADMISSION
          - col(admission_type)
          - col(admission_location)
        time: col(admittime)
        time_format: "%Y-%m-%d %H:%M:%S"
        insurance: insurance
        language: language
        marital_status: marital_status
        race: race
        hadm_id: hadm_id
    hosp/omr:
      omr:
        code: col(result_name)
        text_value: col(result_value)
        time: col(chartdate)
        time_format: "%Y-%m-%d"
    icu/chartevents:
      event:
        code:
          - LAB
          - col(itemid)
          - col(valueuom)
        time: col(charttime)
        time_format: "%Y-%m-%d %H:%M:%S"
    """
)

CUSTOM_EVENT_CONFIG_TEXT = textwrap.dedent(
    """\
    subject_id_col: subject_id
    hosp/admissions:
      admission:
        code:
          - HOSPITAL_ADMISSION
          - col(admission_type)
          - col(admission_location)
        time: col(admittime)
        time_format: "%Y-%m-%d %H:%M:%S"
        hadm_id: hadm_id
      admission_insurance:
        code:
          - INSURANCE
          - col(insurance)
        time: col(admittime)
        time_format: "%Y-%m-%d %H:%M:%S"
        hadm_id: hadm_id
      admission_language:
        code:
          - LANGUAGE
          - col(language)
        time: col(admittime)
        time_format: "%Y-%m-%d %H:%M:%S"
        hadm_id: hadm_id
      admission_marital_status:
        code:
          - MARITAL_STATUS
          - col(marital_status)
        time: col(admittime)
        time_format: "%Y-%m-%d %H:%M:%S"
        hadm_id: hadm_id
      admission_race:
        code:
          - RACE
          - col(race)
        time: col(admittime)
        time_format: "%Y-%m-%d %H:%M:%S"
        hadm_id: hadm_id
    hosp/omr:
      omr:
        code:
          - OMR
          - col(result_name)
        text_value: col(result_value)
        time: col(chartdate)
        time_format: "%Y-%m-%d"
    icu/chartevents:
      event:
        code:
          - CHARTEVENT
          - col(itemid)
          - col(valueuom)
        time: col(charttime)
        time_format: "%Y-%m-%d %H:%M:%S"
    """
)


def _make_repo_setup(repo_dir: Path) -> None:
    (repo_dir / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
    (repo_dir / ".venv" / "bin" / "python").write_text("", encoding="utf-8")
    (repo_dir / ".venv" / "bin" / "MEDS_extract-MIMIC_IV").write_text("", encoding="utf-8")
    (repo_dir / "uv.lock").write_text("# synthetic lock\n", encoding="utf-8")


def _write_repo_configs(
    repo_dir: Path,
    *,
    custom_config_text: str | None = CUSTOM_EVENT_CONFIG_TEXT,
    default_config_text: str = DEFAULT_EVENT_CONFIG_TEXT,
) -> None:
    config_dir = repo_dir / "src" / "MIMIC_IV_MEDS" / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "event_configs.yaml").write_text(default_config_text, encoding="utf-8")
    if custom_config_text is not None:
        (config_dir / "custom_event_configs.yaml").write_text(
            custom_config_text,
            encoding="utf-8",
        )


def _write_codes_table(path: Path) -> None:
    table = pa.table(
        {
            "code": pa.array(
                [
                    "CHARTEVENT//220045//bpm",
                    "OMR//BMI",
                    "INSURANCE//Medicare",
                    "LANGUAGE//ENGLISH",
                    "MARITAL_STATUS//MARRIED",
                    "RACE//WHITE",
                ],
                type=pa.string(),
            ),
            "description": pa.array(
                ["heart rate", "body mass index", "coverage", "language", "status", "race"],
                type=pa.string(),
            ),
            "parent_codes": pa.array(
                [
                    ["PARENT/CHARTEVENT"],
                    ["PARENT/OMR"],
                    ["PARENT/INSURANCE"],
                    ["PARENT/LANGUAGE"],
                    ["PARENT/MARITAL_STATUS"],
                    ["PARENT/RACE"],
                ],
                type=pa.list_(pa.string()),
            ),
            "itemid": pa.array(
                [["220045"], ["BMI"], ["insurance"], ["language"], ["marital_status"], ["race"]],
                type=pa.large_list(pa.large_string()),
            ),
            "valueuom": pa.array(
                [["bpm"], ["kg/m2"], [None], [None], [None], [None]],
                type=pa.large_list(pa.large_string()),
            ),
            "possibly_cpt_code": pa.array(
                [[None], [None], [None], [None], [None], [None]],
                type=pa.large_list(pa.large_string()),
            ),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _write_subject_splits_table(path: Path) -> None:
    table = pa.table(
        {
            "subject_id": pa.array([20, 10, 30], type=pa.int64()),
            "split": pa.array(["tuning", "train", "held_out"], type=pa.string()),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _write_data_table(path: Path, rows: int, *, offset: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    prefixes = [
        "CHARTEVENT//220045//bpm",
        "OMR//BMI",
        "INSURANCE//Medicare",
        "LANGUAGE//ENGLISH",
        "MARITAL_STATUS//MARRIED",
        "RACE//WHITE",
    ]
    pq.write_table(
        pa.table(
            {
                "value": pa.array(list(range(offset, offset + rows)), type=pa.int32()),
                "code": pa.array(
                    [prefixes[(offset + i) % len(prefixes)] for i in range(rows)],
                    type=pa.string(),
                ),
            }
        ),
        path,
    )


def _write_default_style_data_table(path: Path, rows: int, *, offset: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    prefixes = [
        "LAB//220045//bpm",
        "BMI",
        "LAB//50809//mg/dL",
    ]
    pq.write_table(
        pa.table(
            {
                "value": pa.array(list(range(offset, offset + rows)), type=pa.int32()),
                "code": pa.array(
                    [prefixes[(offset + i) % len(prefixes)] for i in range(rows)],
                    type=pa.string(),
                ),
            }
        ),
        path,
    )


def _create_valid_output(repo_dir: Path, output_root: Path) -> None:
    _make_repo_setup(repo_dir)
    _write_repo_configs(repo_dir)

    meds_root = output_root / "MEDS_cohort"
    metadata_dir = meds_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "dataset.json").write_text(
        json.dumps(
            {
                "dataset_name": "MIMIC-IV",
                "dataset_version": "3.1:0.0.7",
                "etl_name": "MEDS_transforms",
                "etl_version": "0.2.4",
                "meds_version": "0.3.3",
                "created_at": "2026-04-07T00:00:00",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_codes_table(metadata_dir / "codes.parquet")
    _write_subject_splits_table(metadata_dir / "subject_splits.parquet")

    _write_data_table(meds_root / "data" / "held_out" / "0.parquet", 3, offset=0)
    _write_data_table(meds_root / "data" / "train" / "0.parquet", 4, offset=3)
    _write_data_table(meds_root / "data" / "tuning" / "0.parquet", 2, offset=1)


def _build_gold_summary(output_root: Path, summary_out: Path) -> None:
    subprocess.run(
        [
            ".venv/bin/python",
            "scripts/mimic_iv_meds/build_reference_summary.py",
            "--output-root",
            str(output_root),
            "--summary-out",
            str(summary_out),
        ],
        check=True,
    )


def _run_verifier(
    repo_dir: Path,
    output_root: Path,
    gold_summary: Path,
    reward_file: Path,
    error_file: Path,
) -> dict:
    subprocess.run(
        [
            ".venv/bin/python",
            "tasks/mimic_iv_meds/tests/verify_output.py",
            "--repo-dir",
            str(repo_dir),
            "--output-root",
            str(output_root),
            "--gold-summary",
            str(gold_summary),
            "--reward-file",
            str(reward_file),
            "--error-analysis-file",
            str(error_file),
        ],
        check=True,
    )
    return json.loads(error_file.read_text(encoding="utf-8"))


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
        output_root / "environment" / "workspace" / "runtime_patch" / "sitecustomize.py"
    ).exists()
    assert not (
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

    assert "inspect the repository" in instruction.lower()
    assert "create a new extraction config" in instruction.lower()
    assert "custom_event_configs.yaml" in instruction
    assert "leave the default config" in instruction.lower()
    assert "separate events at the admission timestamp" in instruction.lower()
    assert "chartevent//" in instruction.lower()
    assert "omr//" in instruction.lower()
    assert "/workspace/MIMIC_IV_MEDS" in instruction
    assert "/workspace/staged_demo/raw_input" in instruction
    assert "/workspace/output/MEDS_cohort" in instruction
    assert "patch_meds_transforms_lock.py" not in instruction
    assert "upstream" not in instruction.lower()
    assert "git checkout 9699e0865b050325459b11f3c4e226a9dbe5b496" in dockerfile
    assert "pyarrow==23.0.1" in dockerfile
    assert "pyyaml==6.0.3" in dockerfile
    assert "ENV PYTHONPATH=/workspace/runtime_patch" in dockerfile
    assert "sitecustomize.py" in dockerfile or "/workspace/runtime_patch" in dockerfile
    assert "missing_custom_config" in verifier
    assert "default_config_modified" in verifier
    assert "custom_config_invalid" in verifier
    assert "custom_config_behavior_missing" in verifier
    assert "metadata_content_mismatch" in verifier
    assert "data_hash_mismatch" in verifier
    assert 'benchmark = "mimic_iv_meds"' in task_toml
    assert "allow_internet = true" in task_toml
    assert "Expected agent workflow" not in workspace_readme
    assert "uv sync" not in workspace_readme
    assert "patch_meds_transforms_lock.py" not in workspace_readme


def test_mimic_iv_meds_verifier_accepts_created_at_and_column_order_variation(tmp_path: Path):
    repo_dir = tmp_path / "workspace" / "MIMIC_IV_MEDS"
    output_root = tmp_path / "workspace" / "output"
    gold_summary = tmp_path / "gold.json"
    reward_file = tmp_path / "logs" / "reward.txt"
    error_file = tmp_path / "logs" / "error_analysis.json"

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)

    metadata_dir = output_root / "MEDS_cohort" / "metadata"
    codes = pq.read_table(metadata_dir / "codes.parquet")
    pq.write_table(
        codes.select(
            ["code", "description", "parent_codes", "possibly_cpt_code", "itemid", "valueuom"]
        ),
        metadata_dir / "codes.parquet",
    )
    dataset_payload = json.loads((metadata_dir / "dataset.json").read_text(encoding="utf-8"))
    dataset_payload["created_at"] = "2030-01-01T00:00:00"
    (metadata_dir / "dataset.json").write_text(
        json.dumps(dataset_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "1.000000"
    assert payload["passed"] is True
    assert payload["failures"] == []


def test_mimic_iv_meds_verifier_detects_metadata_and_data_content_drift(tmp_path: Path):
    repo_dir = tmp_path / "workspace" / "MIMIC_IV_MEDS"
    output_root = tmp_path / "workspace" / "output"
    gold_summary = tmp_path / "gold.json"
    reward_file = tmp_path / "logs" / "reward.txt"
    error_file = tmp_path / "logs" / "error_analysis.json"

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)

    metadata_dir = output_root / "MEDS_cohort" / "metadata"
    pq.write_table(
        pa.table(
            {
                "code": pa.array(
                    [
                        "CHARTEVENT//220045//bpm",
                        "OMR//BMI",
                        "INSURANCE//Medicare",
                        "LANGUAGE//ENGLISH",
                        "MARITAL_STATUS//MARRIED",
                        "RACE//WHITE",
                    ],
                    type=pa.string(),
                ),
                "description": pa.array(
                    ["changed", "body mass index", "coverage", "language", "status", "race"],
                    type=pa.string(),
                ),
                "parent_codes": pa.array(
                    [
                        ["PARENT/CHARTEVENT"],
                        ["PARENT/OMR"],
                        ["PARENT/INSURANCE"],
                        ["PARENT/LANGUAGE"],
                        ["PARENT/MARITAL_STATUS"],
                        ["PARENT/RACE"],
                    ],
                    type=pa.list_(pa.string()),
                ),
                "itemid": pa.array(
                    [["220045"], ["BMI"], ["insurance"], ["language"], ["marital_status"], ["race"]],
                    type=pa.large_list(pa.large_string()),
                ),
                "valueuom": pa.array(
                    [["bpm"], ["kg/m2"], [None], [None], [None], [None]],
                    type=pa.large_list(pa.large_string()),
                ),
                "possibly_cpt_code": pa.array(
                    [[None], [None], [None], [None], [None], [None]],
                    type=pa.large_list(pa.large_string()),
                ),
            }
        ),
        metadata_dir / "codes.parquet",
    )

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    assert payload["passed"] is False
    assert payload["error_taxonomy"]["metadata_content_mismatch"] >= 1

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)
    _write_data_table(output_root / "MEDS_cohort" / "data" / "train" / "0.parquet", 4, offset=2)

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    assert payload["passed"] is False
    assert payload["error_taxonomy"]["data_hash_mismatch"] >= 1


def test_mimic_iv_meds_verifier_requires_uv_setup(tmp_path: Path):
    repo_dir = tmp_path / "workspace" / "MIMIC_IV_MEDS"
    output_root = tmp_path / "workspace" / "output"
    gold_summary = tmp_path / "gold.json"
    reward_file = tmp_path / "logs" / "reward.txt"
    error_file = tmp_path / "logs" / "error_analysis.json"

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)
    (repo_dir / ".venv").rename(repo_dir / ".venv_hidden")

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    assert payload["passed"] is False
    assert payload["error_taxonomy"]["missing_uv_setup"] >= 1


def test_mimic_iv_meds_verifier_requires_custom_config_file(tmp_path: Path):
    repo_dir = tmp_path / "workspace" / "MIMIC_IV_MEDS"
    output_root = tmp_path / "workspace" / "output"
    gold_summary = tmp_path / "gold.json"
    reward_file = tmp_path / "logs" / "reward.txt"
    error_file = tmp_path / "logs" / "error_analysis.json"

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)
    (repo_dir / "src" / "MIMIC_IV_MEDS" / "configs" / "custom_event_configs.yaml").unlink()

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    assert payload["passed"] is False
    assert payload["error_taxonomy"]["missing_custom_config"] >= 1


def test_mimic_iv_meds_verifier_detects_default_or_custom_config_problems(tmp_path: Path):
    repo_dir = tmp_path / "workspace" / "MIMIC_IV_MEDS"
    output_root = tmp_path / "workspace" / "output"
    gold_summary = tmp_path / "gold.json"
    reward_file = tmp_path / "logs" / "reward.txt"
    error_file = tmp_path / "logs" / "error_analysis.json"

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)
    _write_repo_configs(repo_dir, default_config_text=CUSTOM_EVENT_CONFIG_TEXT)

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    assert payload["passed"] is False
    assert payload["error_taxonomy"]["default_config_modified"] >= 1

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)
    _write_repo_configs(
        repo_dir,
        custom_config_text=DEFAULT_EVENT_CONFIG_TEXT,
    )

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    assert payload["passed"] is False
    assert payload["error_taxonomy"]["custom_config_invalid"] >= 1


def test_mimic_iv_meds_verifier_rejects_default_config_style_output(tmp_path: Path):
    repo_dir = tmp_path / "workspace" / "MIMIC_IV_MEDS"
    output_root = tmp_path / "workspace" / "output"
    gold_summary = tmp_path / "gold.json"
    reward_file = tmp_path / "logs" / "reward.txt"
    error_file = tmp_path / "logs" / "error_analysis.json"

    _create_valid_output(repo_dir, output_root)
    _build_gold_summary(output_root, gold_summary)

    metadata_dir = output_root / "MEDS_cohort" / "metadata"
    pq.write_table(
        pa.table(
            {
                "code": pa.array(["LAB//220045//bpm", "BMI"], type=pa.string()),
                "description": pa.array(["heart rate", "body mass index"], type=pa.string()),
                "parent_codes": pa.array(
                    [["PARENT/LAB"], ["PARENT/OMR"]],
                    type=pa.list_(pa.string()),
                ),
                "itemid": pa.array(
                    [["220045"], ["BMI"]],
                    type=pa.large_list(pa.large_string()),
                ),
                "valueuom": pa.array(
                    [["bpm"], ["kg/m2"]],
                    type=pa.large_list(pa.large_string()),
                ),
                "possibly_cpt_code": pa.array(
                    [[None], [None]],
                    type=pa.large_list(pa.large_string()),
                ),
            }
        ),
        metadata_dir / "codes.parquet",
    )
    _write_default_style_data_table(output_root / "MEDS_cohort" / "data" / "held_out" / "0.parquet", 3)
    _write_default_style_data_table(output_root / "MEDS_cohort" / "data" / "train" / "0.parquet", 4)
    _write_default_style_data_table(output_root / "MEDS_cohort" / "data" / "tuning" / "0.parquet", 2)

    payload = _run_verifier(repo_dir, output_root, gold_summary, reward_file, error_file)
    assert reward_file.read_text(encoding="utf-8").strip() == "0.000000"
    assert payload["passed"] is False
    assert payload["error_taxonomy"]["custom_config_behavior_missing"] >= 1
