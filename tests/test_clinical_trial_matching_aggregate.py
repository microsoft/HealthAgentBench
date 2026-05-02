"""Smoke tests for scripts/clinical_trial_matching/aggregate_metric.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGG = REPO_ROOT / "scripts" / "clinical_trial_matching" / "aggregate_metric.py"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def _run(input_path: Path, output_path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(AGG), "-i", str(input_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert output_path.exists(), result.stderr
    return json.loads(output_path.read_text())


def test_pools_ndcg_across_trials(tmp_path: Path) -> None:
    rewards = [
        {
            "reward": 0.8,
            "ndcg_cut_10": 0.8,
            "ndcg_cut_1000": 0.95,
            "recall_1000": 1.0,
            "topic_id": 8,
            "turn_count": 12,
        },
        {
            "reward": 0.4,
            "ndcg_cut_10": 0.4,
            "ndcg_cut_1000": 0.7,
            "recall_1000": 0.85,
            "topic_id": 75,
            "turn_count": 18,
        },
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rewards)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out["mean_ndcg_cut_10"] == 0.6
    assert out["median_ndcg_cut_10"] == 0.6
    assert out["mean_ndcg_cut_1000"] == 0.825
    assert out["mean_recall_1000"] == 0.925
    assert out["n_trials"] == 2
    assert out["mean_turn_count"] == 15.0
    assert out["topic_8_mean_ndcg_cut_10"] == 0.8
    assert out["topic_75_mean_ndcg_cut_10"] == 0.4


def test_handles_bare_scalar_lines(tmp_path: Path) -> None:
    """Falls back gracefully when reward.jsonl just contains numeric scalars."""
    (tmp_path / "rewards.jsonl").write_text("0.5\n0.7\n")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out["n_trials"] == 2
    assert out["mean_ndcg_cut_10"] == 0.6


def test_empty_input(tmp_path: Path) -> None:
    (tmp_path / "rewards.jsonl").write_text("")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out == {"error": "no rewards"}


def test_prefers_run_dir_reward_jsons_over_jsonl(tmp_path: Path) -> None:
    """When the input path is rewards.jsonl inside a Harbor run dir, the
    aggregator scans <run_dir>/<task_*>/verifier/reward.json for richer
    per-trial metrics rather than the bare scalar in rewards.jsonl.
    """
    run_dir = tmp_path / "run_2026"
    run_dir.mkdir()
    for i, ndcg in enumerate([0.8, 0.4]):
        td = run_dir / f"task_{i}__abc{i}"
        (td / "verifier").mkdir(parents=True)
        (td / "verifier" / "reward.json").write_text(
            json.dumps(
                {
                    "reward": ndcg,
                    "ndcg_cut_10": ndcg,
                    "ndcg_cut_1000": 0.9,
                    "recall_1000": 0.95,
                    "topic_id": 8 + i,
                }
            )
        )
    (run_dir / "rewards.jsonl").write_text("0.0\n0.0\n")
    out = _run(run_dir / "rewards.jsonl", tmp_path / "metric.json")
    assert out["mean_ndcg_cut_10"] == 0.6
    assert out["topic_8_mean_ndcg_cut_10"] == 0.8
    assert out["topic_9_mean_ndcg_cut_10"] == 0.4
