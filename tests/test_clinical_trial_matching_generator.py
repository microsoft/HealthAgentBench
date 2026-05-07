"""Smoke tests for scripts/clinical_trial_matching/generate_harbor_tasks.py.

Network-touching (host prefetch + topics/qrels download) is mocked so
the test runs offline. The generator's pure-logic functions
(parse_topics, parse_qrels_for_topic, _build_task) are covered.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(
    0, str(REPO_ROOT / "scripts" / "clinical_trial_matching")
)

import generate_harbor_tasks as gen  # noqa: E402


def _toy_topics_xml(path: Path) -> None:
    path.write_text(
        '<topics task="2021 TREC Clinical Trials">'
        '<topic number="1">A 30-year-old man with diabetes</topic>'
        '<topic number="2">A 45-year-old woman with breast cancer</topic>'
        "</topics>"
    )


def _toy_qrels(path: Path) -> None:
    rows = [
        "1 0 NCT00001 2",
        "1 0 NCT00002 1",
        "1 0 NCT00003 0",
        "2 0 NCT00010 2",
        "2 0 NCT00011 0",
    ]
    path.write_text("\n".join(rows) + "\n")


def test_parse_topics(tmp_path: Path) -> None:
    p = tmp_path / "topics.xml"
    _toy_topics_xml(p)
    topics = gen.parse_topics(p)
    assert set(topics) == {1, 2}
    assert "diabetes" in topics[1]


def test_parse_qrels_for_topic(tmp_path: Path) -> None:
    p = tmp_path / "qrels.txt"
    _toy_qrels(p)
    rows1 = gen.parse_qrels_for_topic(p, 1)
    assert len(rows1) == 3
    grades = {nct: g for nct, g in rows1}
    assert grades == {"NCT00001": 2, "NCT00002": 1, "NCT00003": 0}
    rows2 = gen.parse_qrels_for_topic(p, 2)
    assert len(rows2) == 2


def test_build_task_writes_expected_files(tmp_path: Path) -> None:
    task_root = tmp_path / "task_1"
    judged = [("NCT00001", 2), ("NCT00002", 1), ("NCT00003", 0)]
    gen._build_task(
        task_root,
        topic_id=1,
        topic_text="A 30-year-old man with diabetes",
        judged=judged,
        host_cache_path=tmp_path / "fake_cache",
    )

    # Top-level files
    assert (task_root / "task.toml").exists()
    instr = (task_root / "instruction.md").read_text()
    assert "Patient-to-Trial Eligibility" in instr
    # Source obfuscation: must not name TREC or ClinicalTrials.gov in
    # agent-visible artifacts.
    assert "TREC" not in instr
    assert "qrels" not in instr.lower()

    # Workspace files (agent-visible)
    ws = task_root / "environment" / "workspace"
    assert (ws / "topic.txt").read_text().startswith("A 30-year-old")
    assert (ws / "topic_id.txt").read_text().strip() == "1"
    nct_lines = (ws / "trial_ncts.txt").read_text().strip().split()
    assert sorted(nct_lines) == ["NCT00001", "NCT00002", "NCT00003"]
    assert (ws / "fetch_trials.py").exists()

    # Tests dir (verifier-only)
    td = task_root / "tests"
    assert (td / "qrels.txt").read_text().count("\n") == 3
    assert (td / "harbor_evaluator.py").exists()
    assert (td / "verify.py").exists()
    assert (td / "test.sh").exists()
    # test.sh should be executable
    assert (td / "test.sh").stat().st_mode & 0o111

    # Environment files (two-service compose: bootstrap + main)
    env_dir = task_root / "environment"
    dockerfile = (env_dir / "Dockerfile").read_text()
    # No ENTRYPOINT directive — Harbor's base compose layer overrides main's
    # command to ``sleep infinity``. (The substring is allowed in comments.)
    assert "ENTRYPOINT [" not in dockerfile
    assert 'CMD ["/bin/bash"]' not in dockerfile
    assert "COPY environment/bootstrap.sh /bootstrap.sh" in dockerfile
    compose = (env_dir / "docker-compose.yaml").read_text()
    assert "/data/_cache:rw" in compose
    assert str(tmp_path / "fake_cache") in compose
    assert "service_completed_successfully" in compose
    assert "workspace-data:/workspace/data" in compose
    bootstrap = (env_dir / "bootstrap.sh").read_text()
    assert "flock 9" in bootstrap
    assert "chmod a-w" in bootstrap  # per-file freeze, not directory-wide
    # No bootstrap-sentinel files in /workspace/ under the new pattern.
    assert ".bootstrap_required" not in bootstrap
    assert ".bootstrap_done" not in bootstrap
    assert (env_dir / "bootstrap.sh").stat().st_mode & 0o111
