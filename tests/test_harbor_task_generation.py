import json
import subprocess
from pathlib import Path


def _write_manifest(path: Path, tasks: list[tuple[str, str]]) -> None:
    blocks = []
    for task_id, source_group in tasks:
        blocks.append(
            "\n".join(
                [
                    f"  - task_id: {task_id}",
                    "    category: factual_qa",
                    "    difficulty: easy",
                    f"    instruction: synthetic task for {task_id}",
                    "    task_type: query",
                    f"    source_group: {source_group}",
                    "    source_benchmark: medagentbench",
                ]
            )
        )
    path.write_text("tasks:\n" + "\n".join(blocks) + "\n", encoding="utf-8")


def test_generate_harbor_meta_task_materializes_expected_layout(tmp_path: Path):
    input_root = tmp_path / "tasks"
    manifest_dir = input_root / "factual_qa" / "sources" / "medagentbench"
    manifest_dir.mkdir(parents=True)
    _write_manifest(
        manifest_dir / "std.yaml",
        [("task1_1", "task1"), ("task2_1", "task2")],
    )

    output_root = tmp_path / "harbor_tasks" / "medagentbench"

    subprocess.run(
        [
            ".venv/bin/python",
            "scripts/medagentbench/generate_harbor_tasks.py",
            "--input-root",
            str(input_root),
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
    assert (output_root / "environment" / "Dockerfile").exists()
    assert (output_root / "environment" / "docker-compose.yaml").exists()
    assert (output_root / "environment" / "workspace" / "scripts" / "fhir_tools.py").exists()
    assert not (output_root / "environment" / "workspace" / "submission.json").exists()
    assert (output_root / "tests" / "test.sh").exists()
    assert (output_root / "tests" / "verify_meta_task.py").exists()
    assert not (output_root / "tests" / "__pycache__").exists()

    payload = json.loads((output_root / "benchmark_tasks.json").read_text(encoding="utf-8"))
    assert [row["task_id"] for row in payload["tasks"]] == ["task1_1", "task2_1"]

    compose_text = (output_root / "environment" / "docker-compose.yaml").read_text(encoding="utf-8")
    assert "jyxsu6/medagentbench@sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966" in compose_text
    assert "fhir-ready" in compose_text
    assert "service_completed_successfully" in compose_text


def test_generate_harbor_meta_task_is_deterministic(tmp_path: Path):
    input_root = tmp_path / "tasks"
    manifest_dir = input_root / "factual_qa" / "sources" / "medagentbench"
    manifest_dir.mkdir(parents=True)
    _write_manifest(
        manifest_dir / "std.yaml",
        [("task1_1", "task1"), ("task2_1", "task2")],
    )

    output_root = tmp_path / "harbor_tasks" / "medagentbench"
    cmd = [
        ".venv/bin/python",
        "scripts/medagentbench/generate_harbor_tasks.py",
        "--input-root",
        str(input_root),
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
    input_root = tmp_path / "tasks"
    manifest_dir = input_root / "factual_qa" / "sources" / "medagentbench"
    manifest_dir.mkdir(parents=True)
    _write_manifest(manifest_dir / "std.yaml", [("task1_1", "task1")])

    proc = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/medagentbench/generate_harbor_tasks.py",
            "--input-root",
            str(input_root),
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
