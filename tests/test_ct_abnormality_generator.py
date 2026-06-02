"""Smoke tests for scripts/ct_abnormality/generate_harbor_tasks.py.

These tests exercise the generator against the committed (volume-ID-only)
manifest and check that the resulting task tree is well-formed for the
runtime-gold-derivation design — without running Harbor. Gold is NOT generated
or committed here; it is derived in-container at run time, so these tests assert
the *plumbing* (no committed gold.json, the derivation module shipped into the
image, the bootstrap wired to download the report + derive).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GEN = REPO_ROOT / "scripts" / "ct_abnormality" / "generate_harbor_tasks.py"
MANIFEST = REPO_ROOT / "scripts" / "ct_abnormality" / "assets" / "manifest.yaml"

EXPECTED_TASKS = {
    "valid_670_a_1", "valid_304_a_1", "valid_81_a_1", "valid_16_a_1",
    "valid_137_a_1", "valid_481_a_2", "valid_636_a_1", "valid_265_a_2",
    "valid_46_a_1", "valid_144_a_1",
}


def _generate(tmp_path: Path) -> Path:
    tasks_root = tmp_path / "tasks_ct_interp"
    subprocess.run(
        [sys.executable, str(GEN), "--manifest", str(MANIFEST), "--tasks-root", str(tasks_root)],
        check=True,
    )
    return tasks_root


def _tasks(root: Path):
    return [p for p in root.iterdir() if p.is_dir() and p.name.startswith("valid_")]


def test_ten_tasks_produced(tmp_path: Path) -> None:
    assert len(_tasks(_generate(tmp_path))) == 10


def test_task_dirs_are_volume_stems(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    assert {p.name for p in _tasks(root)} == EXPECTED_TASKS


def test_task_tree_required_files_exist(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    for task_dir in _tasks(root):
        for relative in [
            "task.toml",
            "instruction.md",
            "environment/Dockerfile",
            "environment/docker-compose.yaml",
            "environment/bootstrap.sh",
            "environment/gold_derivation.py",  # shipped into image for runtime derivation
            "tests/harbor_evaluator.py",
            "tests/verify.py",
            "tests/test.sh",
        ]:
            assert (task_dir / relative).exists(), f"missing {relative} in {task_dir.name}"


def test_gold_json_is_not_committed(tmp_path: Path) -> None:
    """Gold is derived in-container at run time; the generator must NOT write a
    committed gold.json (it would redistribute the answer key / report text)."""
    root = _generate(tmp_path)
    for task_dir in _tasks(root):
        assert not (task_dir / "tests" / "gold.json").exists(), (
            f"{task_dir.name}: gold.json must be runtime-derived, not generated"
        )


def test_bootstrap_wires_runtime_gold_derivation(tmp_path: Path) -> None:
    """bootstrap.sh encodes the volume + reports path and invokes the phrase-rule
    derivation to produce gold.json + labels.txt at run time (no baked labels)."""
    root = _generate(tmp_path)
    bootstrap = (root / "valid_670_a_1" / "environment" / "bootstrap.sh").read_text()
    assert 'VOLUME_NAME="valid_670_a_1.nii.gz"' in bootstrap
    assert "validation_reports.csv" in bootstrap  # reports CSV downloaded
    assert "gold_derivation.py" in bootstrap       # derivation invoked
    assert "/tests/gold.json" in bootstrap
    assert "/workspace/data/labels.txt" in bootstrap
    # No baked per-task label list anymore.
    assert "__LABELS_LIST__" not in bootstrap


def test_dockerfile_ships_gold_derivation(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    dockerfile = (root / "valid_670_a_1" / "environment" / "Dockerfile").read_text()
    assert "COPY environment/gold_derivation.py" in dockerfile


def test_compose_two_service_dependency_and_tests_mount(tmp_path: Path) -> None:
    """bootstrap + main pair; main depends on bootstrap; bootstrap (not main)
    mounts tests/ RW so it can write the runtime gold.json."""
    root = _generate(tmp_path)
    compose = (root / "valid_670_a_1" / "environment" / "docker-compose.yaml").read_text()
    assert "bootstrap:" in compose and "main:" in compose
    assert "service_completed_successfully" in compose
    assert "workspace-data:/workspace/data" in compose
    assert "../tests:/tests:rw" in compose  # bootstrap writes gold.json here


def test_compose_uses_env_file_and_relative_cache(tmp_path: Path) -> None:
    """HF credential via env_file (.env), repo-relative cache bind, no host
    token mount — required for one-click portable runs."""
    root = _generate(tmp_path)
    compose = (root / "valid_670_a_1" / "environment" / "docker-compose.yaml").read_text()
    assert "env_file:" in compose
    assert "../../../../.env" in compose
    assert "../../../../scripts/ct_abnormality/assets/raw_cache:/data/_cache:rw" in compose
    assert ".cache/huggingface/token" not in compose


def test_bootstrap_reads_hf_token_env(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    bootstrap = (root / "valid_670_a_1" / "environment" / "bootstrap.sh").read_text()
    assert "HF_TOKEN" in bootstrap
    assert "/root/.cache/huggingface/token" not in bootstrap


def test_no_absolute_host_paths_in_generated_tree(tmp_path: Path) -> None:
    """Portability guard (benchmark_addition_workflow.md §3 rule 5): nothing in
    the generated task tree may bake in an absolute host path."""
    root = _generate(tmp_path)
    offenders: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            if str(tmp_path) in line or "/home/" in line:
                offenders.append(f"{path.relative_to(root)}:{lineno}: {line.strip()}")
    assert not offenders, "absolute host paths leaked into generated tasks:\n" + "\n".join(offenders)


def test_evaluated_findings_are_seventeen() -> None:
    """The evaluated-category schema lives in gold_derivation.FINDINGS (17;
    Pulmonary fibrotic sequela excluded)."""
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "ct_abnormality"))
    from gold_derivation import FINDINGS  # noqa: E402

    assert len(FINDINGS) == 17
    assert "Pulmonary fibrotic sequela" not in FINDINGS
