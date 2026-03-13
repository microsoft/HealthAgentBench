import json
import subprocess
from pathlib import Path


def _write_raw_tasks(path: Path, tasks: list[dict]) -> None:
    path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")


def test_generate_harbor_meta_task_materializes_expected_layout(tmp_path: Path):
    input_json = tmp_path / "test_data_v2.json"
    _write_raw_tasks(
        input_json,
        [
            {
                "id": "task1_1",
                "instruction": "synthetic task1",
                "context": "ctx1",
                "sol": ["S1"],
                "eval_MRN": "S1",
            },
            {
                "id": "task2_1",
                "instruction": "synthetic task2",
                "context": "ctx2",
                "sol": [42],
                "eval_MRN": "S2",
            },
        ],
    )

    output_root = tmp_path / "harbor_tasks" / "medagentbench"

    subprocess.run(
        [
            ".venv/bin/python",
            "scripts/medagentbench/generate_harbor_tasks.py",
            "--input-json",
            str(input_json),
            "--output-root",
            str(output_root),
            "--selected-task-ids",
            "task1_1,task2_1",
        ],
        check=True,
    )

    assert output_root.exists()
    assert (output_root / "instruction.md").exists()
    assert (output_root / "task.toml").exists()
    assert (output_root / "benchmark_tasks.json").exists()
    assert (output_root / "submission_template.json").exists()
    assert (output_root / "environment" / "workspace" / "scripts" / "fhir_primitives.py").exists()
    assert not (output_root / "environment" / "workspace" / "action_payload_templates.json").exists()
    assert not (output_root / "environment" / "workspace" / "submission.json").exists()
    assert (output_root / "tests" / "test.sh").exists()
    assert (output_root / "tests" / "verify_meta_task.py").exists()
    assert (output_root / "tests" / "task_answer_key.json").exists()

    benchmark_payload = json.loads((output_root / "benchmark_tasks.json").read_text(encoding="utf-8"))
    assert [row["task_id"] for row in benchmark_payload["tasks"]] == ["task1_1", "task2_1"]
    assert set(benchmark_payload["tasks"][0]) == {
        "task_id",
        "category",
        "difficulty",
        "instruction",
    }

    submission_template = json.loads((output_root / "submission_template.json").read_text(encoding="utf-8"))
    assert submission_template[0]["task_id"] == "task1_1"
    assert submission_template[0]["final_answer"] == ""
    assert submission_template[0]["payload"] is None
    assert "sol" not in submission_template[0]
    assert "eval_MRN" not in submission_template[0]

    compose_text = (output_root / "environment" / "docker-compose.yaml").read_text(encoding="utf-8")
    assert "jyxsu6/medagentbench@sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966" in compose_text
    assert "fhir-ready" in compose_text


def test_generate_harbor_meta_task_is_deterministic(tmp_path: Path):
    input_json = tmp_path / "test_data_v2.json"
    _write_raw_tasks(
        input_json,
        [
            {
                "id": "task1_1",
                "instruction": "synthetic task1",
                "context": "ctx1",
                "sol": ["S1"],
                "eval_MRN": "S1",
            },
            {
                "id": "task2_1",
                "instruction": "synthetic task2",
                "context": "ctx2",
                "sol": [42],
                "eval_MRN": "S2",
            },
        ],
    )

    output_root = tmp_path / "harbor_tasks" / "medagentbench"
    cmd = [
        ".venv/bin/python",
        "scripts/medagentbench/generate_harbor_tasks.py",
        "--input-json",
        str(input_json),
        "--output-root",
        str(output_root),
        "--selected-task-ids",
        "task1_1,task2_1",
    ]

    subprocess.run(cmd, check=True)
    first_snapshot = {
        path.relative_to(output_root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(output_root.rglob("*"))
        if path.is_file()
    }

    subprocess.run(cmd, check=True)
    second_snapshot = {
        path.relative_to(output_root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(output_root.rglob("*"))
        if path.is_file()
    }

    assert first_snapshot == second_snapshot


def test_generate_harbor_meta_task_rejects_unknown_selected_ids(tmp_path: Path):
    input_json = tmp_path / "test_data_v2.json"
    _write_raw_tasks(
        input_json,
        [
            {
                "id": "task1_1",
                "instruction": "synthetic task1",
                "context": "ctx1",
                "sol": ["S1"],
                "eval_MRN": "S1",
            }
        ],
    )

    proc = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/medagentbench/generate_harbor_tasks.py",
            "--input-json",
            str(input_json),
            "--output-root",
            str(tmp_path / "out" / "medagentbench"),
            "--selected-task-ids",
            "task1_1,task2_1",
        ],
        text=True,
        capture_output=True,
    )

    assert proc.returncode != 0
    assert "Unknown selected task IDs: task2_1" in proc.stderr
