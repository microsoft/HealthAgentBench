"""Tests for scripts/mimic_iv_dq/generate_harbor_tasks.py."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts" / "mimic_iv_dq"
RAW_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "mimic_iv_dq" / "raw"

sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def generated_tasks(tmp_path: Path) -> Path:
    """Run the generator with fixture data into tmp_path/tasks_root and return that path."""
    # Stage labels into assets/labels by running the corruption pipeline against
    # the offline fixture, so the generator does not try to hit PhysioNet.
    from stage_data import main as stage_main

    labels_dir = tmp_path / "labels_pool"
    labels_dir.mkdir()
    configs = yaml.safe_load(
        (SCRIPTS_DIR / "assets" / "task_configs.yaml").read_text()
    )["tasks"]
    for cfg in configs:
        slice_path = tmp_path / f"{cfg['id']}_slice.yaml"
        slice_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        out_dir = tmp_path / cfg["id"]
        stage_main(
            [
                "--config",
                str(slice_path),
                "--output-dir",
                str(out_dir),
                "--input-dir",
                str(RAW_FIXTURE),
                "--labels-output",
                str(labels_dir / f"{cfg['id']}.csv"),
                "--no-duckdb",
            ]
        )

    # Move the generated labels into the canonical assets dir for the
    # generator to pick up.
    target = SCRIPTS_DIR / "assets" / "labels"
    target.mkdir(parents=True, exist_ok=True)
    backups = []
    for src in labels_dir.iterdir():
        dst = target / src.name
        if dst.exists():
            backup = dst.with_suffix(".csv.test_bak")
            shutil.move(dst, backup)
            backups.append((dst, backup))
        shutil.copy(src, dst)

    output_root = tmp_path / "tasks_root"
    from generate_harbor_tasks import main as gen_main

    gen_main(["--output-root", str(output_root)])

    yield output_root

    # Restore any backed-up labels so this test never permanently mutates
    # checked-in artifacts. New labels we created (no backup) are deleted.
    for dst, backup in backups:
        shutil.move(backup, dst)
    for src in labels_dir.iterdir():
        canonical = target / src.name
        if canonical.exists() and (dst := canonical) not in dict(backups):
            # Only delete if we wrote it in this test (no backup means no prior file).
            if not any(canonical == d for d, _ in backups):
                # There may have been no prior file; ensure idempotence by checking
                # whether a backup exists for it. If no backup, delete.
                if not canonical.with_suffix(".csv.test_bak").exists():
                    canonical.unlink()


def test_generate_creates_all_four_tasks(generated_tasks: Path) -> None:
    expected_ids = sorted(
        [
            "task_impossible_value",
            "task_inconsistency",
            "task_demographic_conflict",
            "task_combined",
        ]
    )
    actual = sorted(p.name for p in generated_tasks.iterdir() if p.is_dir())
    assert actual == expected_ids


def test_each_task_has_required_files(generated_tasks: Path) -> None:
    for task_dir in sorted(p for p in generated_tasks.iterdir() if p.is_dir()):
        assert (task_dir / "task.toml").exists(), f"{task_dir.name}: task.toml missing"
        assert (task_dir / "instruction.md").exists(), f"{task_dir.name}: instruction missing"
        assert (task_dir / "environment" / "Dockerfile").exists()
        assert (task_dir / "environment" / "workspace" / "README.md").exists()
        assert (task_dir / "environment" / "workspace" / "stage_data.py").exists()
        assert (task_dir / "environment" / "workspace" / "inject.py").exists()
        assert (task_dir / "environment" / "workspace" / "task_config.yaml").exists()
        assert (task_dir / "environment" / "build_inputs" / "labels.csv").exists()
        assert (task_dir / "tests" / "test.sh").exists()
        assert (task_dir / "tests" / "verify.py").exists()
        assert (task_dir / "tests" / "harbor_evaluator.py").exists()
        assert (task_dir / "tests" / "labels.csv").exists()


def test_generated_dockerfile_does_not_bake_labels_into_image(generated_tasks: Path) -> None:
    """Labels.csv must be COPY'd transiently (e.g., to /tmp/build_labels.csv)
    and removed in the same RUN layer that uses it. The HOST-side tests/
    directory is mounted by Harbor at verifier time — the image itself
    must not contain a persistent labels file.
    """
    for task_dir in generated_tasks.iterdir():
        if not task_dir.is_dir():
            continue
        text = (task_dir / "environment" / "Dockerfile").read_text()
        # Build-time copy goes to /tmp/build_labels.csv (transient).
        assert "/tmp/build_labels.csv" in text, (
            f"{task_dir.name}: expected build-time COPY to /tmp/build_labels.csv"
        )
        # And is rm'd in the same RUN that uses it.
        assert "rm /tmp/build_labels.csv" in text, (
            f"{task_dir.name}: build-time labels copy must be removed in-layer"
        )
        # Never persists labels at /tests/labels.csv inside the image.
        assert "/tests/labels.csv" not in text, (
            f"{task_dir.name}: image must NOT bake /tests/labels.csv"
        )


def test_generated_workspace_filenames(generated_tasks: Path) -> None:
    """Workspace files keep their canonical names so Python imports resolve at
    Docker build time. The Dockerfile rm-step deletes them after staging.
    """
    for task_dir in generated_tasks.iterdir():
        if not task_dir.is_dir():
            continue
        ws = task_dir / "environment" / "workspace"
        assert (ws / "stage_data.py").exists()
        assert (ws / "inject.py").exists()
        assert (ws / "task_config.yaml").exists()


def test_each_task_has_distinct_seed(generated_tasks: Path) -> None:
    seeds = []
    for task_dir in sorted(p for p in generated_tasks.iterdir() if p.is_dir()):
        cfg = yaml.safe_load(
            (task_dir / "environment" / "workspace" / "task_config.yaml").read_text()
        )
        seeds.append(cfg["seed"])
    # Seeds 0,2,3,4 in task_configs.yaml — seed=1 was removed with
    # task_temporal_violation.
    assert sorted(seeds) == [0, 2, 3, 4]


def test_each_per_family_task_has_one_injector(generated_tasks: Path) -> None:
    """Per-family tasks have exactly one injector; task_combined has all three."""
    family_singletons = {
        "task_impossible_value": "impossible_value",
        "task_inconsistency": "inconsistency",
        "task_demographic_conflict": "demographic_conflict",
    }
    for task_dir in sorted(p for p in generated_tasks.iterdir() if p.is_dir()):
        cfg = yaml.safe_load(
            (task_dir / "environment" / "workspace" / "task_config.yaml").read_text()
        )
        if task_dir.name in family_singletons:
            assert len(cfg["injectors"]) == 1
            assert cfg["injectors"][0]["family"] == family_singletons[task_dir.name]
        elif task_dir.name == "task_combined":
            families = [s["family"] for s in cfg["injectors"]]
            assert set(families) == {
                "impossible_value",
                "inconsistency",
                "demographic_conflict",
            }
        else:
            raise AssertionError(f"unexpected task name: {task_dir.name}")


def test_per_task_instruction_only_lists_its_families(generated_tasks: Path) -> None:
    """Each per-family task's instruction.md mentions only that family's
    category description, not the others.
    """
    keywords = {
        "impossible_value": "Impossible values",
        "temporal_violation": "Temporal inconsistencies",
        "inconsistency": "Conflicting / duplicate records",
        "demographic_conflict": "Demographic contradictions",
    }
    for task_dir in sorted(p for p in generated_tasks.iterdir() if p.is_dir()):
        cfg = yaml.safe_load(
            (task_dir / "environment" / "workspace" / "task_config.yaml").read_text()
        )
        instr = (task_dir / "instruction.md").read_text()
        present_families = {s["family"] for s in cfg["injectors"]}
        for fam, kw in keywords.items():
            if fam in present_families:
                assert kw in instr, f"{task_dir.name}: '{kw}' should appear (family={fam})"
            else:
                assert kw not in instr, (
                    f"{task_dir.name}: '{kw}' should NOT appear (family {fam} is not in this task)"
                )


def test_dockerfile_uses_transient_build_labels(generated_tasks: Path) -> None:
    """The build COPYs labels to /tmp/build_labels.csv only — never into /tests/."""
    for task_dir in generated_tasks.iterdir():
        if not task_dir.is_dir():
            continue
        text = (task_dir / "environment" / "Dockerfile").read_text()
        assert "COPY build_inputs/labels.csv /tmp/build_labels.csv" in text


def test_labels_csv_non_empty(generated_tasks: Path) -> None:
    for task_dir in generated_tasks.iterdir():
        if not task_dir.is_dir():
            continue
        df = pd.read_csv(task_dir / "tests" / "labels.csv", dtype=str, keep_default_na=False)
        # Even on a tiny offline fixture, every task produces at least one
        # corrupted row — except possibly tasks whose target table is the
        # near-empty ``icustays`` (none of our tasks do that).
        assert not df.empty, f"{task_dir.name}: labels.csv is empty"
