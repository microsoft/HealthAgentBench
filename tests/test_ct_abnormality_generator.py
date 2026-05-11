"""Smoke tests for scripts/ct_abnormality/generate_harbor_tasks.py.

These tests exercise the generator against the committed manifest and check
that the resulting task tree is well-formed (without actually running Harbor).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
GEN = REPO_ROOT / "scripts" / "ct_abnormality" / "generate_harbor_tasks.py"
MANIFEST = REPO_ROOT / "scripts" / "ct_abnormality" / "assets" / "manifest.yaml"


def _generate(tmp_path: Path) -> Path:
    tasks_root = tmp_path / "tasks_ct_interp"
    subprocess.run(
        [
            sys.executable,
            str(GEN),
            "--manifest",
            str(MANIFEST),
            "--tasks-root",
            str(tasks_root),
            "--host-cache",
            str(tmp_path / "fake_cache"),
        ],
        check=True,
    )
    return tasks_root


def test_ten_tasks_produced(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    task_dirs = sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("valid_"))
    assert len(task_dirs) == 10


def test_task_tree_required_files_exist(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    for task_dir in (p for p in root.iterdir() if p.name.startswith("valid_")):
        for relative in [
            "task.toml",
            "instruction.md",
            "environment/Dockerfile",
            "environment/docker-compose.yaml",
            "environment/bootstrap.sh",
            "tests/gold.json",
            "tests/harbor_evaluator.py",
            "tests/verify.py",
            "tests/test.sh",
        ]:
            assert (task_dir / relative).exists(), f"missing {relative} in {task_dir.name}"


def test_gold_json_matches_manifest(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    by_id = {entry["task_id"]: entry for entry in manifest["volumes"]}
    for task_dir in (p for p in root.iterdir() if p.name.startswith("valid_")):
        gold = json.loads((task_dir / "tests" / "gold.json").read_text())
        manifest_entry = by_id[task_dir.name]
        assert gold["volume_name"] == manifest_entry["volume_name"]
        # Same labels, same gold values, same evidence strings.
        gold_labels = {(lab["name"], int(lab["gold"]), lab["evidence"]) for lab in gold["labels"]}
        manifest_labels = {
            (lab["name"], int(lab["gold"]), lab["evidence"])
            for lab in manifest_entry["labels"]
        }
        assert gold_labels == manifest_labels


def test_pulmonary_fibrotic_sequela_not_in_any_task(tmp_path: Path) -> None:
    """The 18th CT-RATE category was dropped because no volume retained it."""
    root = _generate(tmp_path)
    for task_dir in (p for p in root.iterdir() if p.name.startswith("valid_")):
        gold = json.loads((task_dir / "tests" / "gold.json").read_text())
        names = {lab["name"] for lab in gold["labels"]}
        assert "Pulmonary fibrotic sequela" not in names


def test_bootstrap_embeds_volume_name_and_labels(tmp_path: Path) -> None:
    """The generated bootstrap.sh must encode the per-task volume + labels."""
    root = _generate(tmp_path)
    # Task directories are named after the CT-RATE volume stem (canonical task_id).
    task1 = root / "valid_670_a_1"
    bootstrap = (task1 / "environment" / "bootstrap.sh").read_text()
    # valid_670_a_1 retained labels: Cardiomegaly, Pericardial effusion,
    # Lymphadenopathy, Lung nodule.
    assert 'VOLUME_NAME="valid_670_a_1.nii.gz"' in bootstrap
    assert "Cardiomegaly" in bootstrap
    assert "Pericardial effusion" in bootstrap
    assert "Lymphadenopathy" in bootstrap
    assert "Lung nodule" in bootstrap


def test_compose_uses_two_service_dependency(tmp_path: Path) -> None:
    """docker-compose.yaml declares a bootstrap + main pair where main depends
    on bootstrap completing successfully (medagentbench pattern). This is the
    contract that lets us drop the in-wrapper /workspace/.bootstrap_done wait.
    """
    root = _generate(tmp_path)
    compose = (root / "valid_670_a_1" / "environment" / "docker-compose.yaml").read_text()
    assert "bootstrap:" in compose
    assert "main:" in compose
    assert "service_completed_successfully" in compose
    assert "workspace-data:/workspace/data" in compose
    # No references to the old sentinel files in the new compose path.
    assert ".bootstrap_required" not in compose
    assert ".bootstrap_done" not in compose


def test_task_dirs_are_volume_stems(tmp_path: Path) -> None:
    """Every generated task directory name is exactly the CT-RATE volume stem."""
    root = _generate(tmp_path)
    expected = {
        "valid_670_a_1", "valid_304_a_1", "valid_81_a_1", "valid_16_a_1",
        "valid_137_a_1", "valid_481_a_2", "valid_636_a_1", "valid_265_a_2",
        "valid_46_a_1", "valid_144_a_1",
    }
    actual = {p.name for p in root.iterdir() if p.is_dir() and p.name.startswith("valid_")}
    assert actual == expected


def test_evaluated_label_set_size_seventeen(tmp_path: Path) -> None:
    """The manifest declares 17 evaluated categories (Pulm fibrotic seq dropped)."""
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert len(manifest["evaluated_labels"]) == 17
    assert "Pulmonary fibrotic sequela" not in manifest["evaluated_labels"]
