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


def _reward(
    *,
    ndcg: float,
    f1: float,
    p: float,
    r: float,
    n_pred: int,
    tp: int,
    fp: int,
    fn: int,
    topic: int,
    turns: int,
) -> dict:
    return {
        "reward": ndcg,
        "ndcg_at_10": ndcg,
        "dcg_at_10": ndcg * 4.0,
        "precision_at_10": p,
        "recall_at_10": r,
        "f1": f1,
        "precision": p,
        "recall": r,
        "n_predicted": n_pred,
        "n_true_positives": tp,
        "n_false_positives": fp,
        "n_false_negatives": fn,
        "topic_id": topic,
        "turn_count": turns,
    }


def test_pools_metrics_across_trials(tmp_path: Path) -> None:
    rewards = [
        _reward(ndcg=0.9, f1=0.8, p=0.75, r=0.857, n_pred=4, tp=3, fp=1, fn=0, topic=8, turns=12),
        _reward(ndcg=0.5, f1=0.5, p=0.5, r=0.5, n_pred=4, tp=2, fp=2, fn=2, topic=75, turns=18),
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rewards)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")

    assert out["mean_ndcg_at_10"] == pytest_round(0.7)
    assert out["mean_f1"] == pytest_round(0.65)
    assert out["mean_precision"] == pytest_round(0.625)
    # Micro: 5 TP / 8 predicted = 0.625 precision; 5 TP / 7 actual eligible.
    assert out["micro_precision"] == 0.625
    assert out["micro_recall"] == round(5 / 7, 4)
    assert out["n_trials"] == 2
    assert out["n_total_true_positives"] == 5
    assert out["n_total_false_positives"] == 3
    assert out["mean_turn_count"] == 15.0
    assert out["topic_8_mean_ndcg_at_10"] == 0.9
    assert out["topic_75_mean_ndcg_at_10"] == 0.5
    assert out["topic_8_mean_f1"] == 0.8


def test_handles_bare_scalar_lines(tmp_path: Path) -> None:
    """Bare scalar lines fall through ``ndcg_at_10`` lookup to ``reward``."""
    (tmp_path / "rewards.jsonl").write_text("0.5\n0.7\n")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out["n_trials"] == 2
    assert out["mean_ndcg_at_10"] == 0.6


def test_empty_input(tmp_path: Path) -> None:
    (tmp_path / "rewards.jsonl").write_text("")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out == {"error": "no rewards"}


def test_prefers_run_dir_reward_jsons_over_jsonl(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_2026"
    run_dir.mkdir()
    for i, ndcg in enumerate([0.9, 0.4]):
        td = run_dir / f"task_{i}__abc{i}"
        (td / "verifier").mkdir(parents=True)
        (td / "verifier" / "reward.json").write_text(
            json.dumps(
                _reward(
                    ndcg=ndcg, f1=0.5, p=0.9, r=0.7,
                    n_pred=5, tp=4, fp=1, fn=2, topic=8 + i, turns=10,
                )
            )
        )
    (run_dir / "rewards.jsonl").write_text("0.0\n0.0\n")
    out = _run(run_dir / "rewards.jsonl", tmp_path / "metric.json")
    assert out["mean_ndcg_at_10"] == 0.65
    assert out["topic_8_mean_ndcg_at_10"] == 0.9
    assert out["topic_9_mean_ndcg_at_10"] == 0.4


def test_success_and_pass_rate_aggregate(tmp_path: Path) -> None:
    """`success` (integer pass count) and `pass_rate` (fraction) are
    derived from per-trial reward == 1.0. The aggregate emits both so
    `--metric-to-report success` shows the integer count.
    """
    rewards = [
        # 2 of 3 trials hit NDCG@10 == 1.0 (reward=1.0).
        {**_reward(ndcg=1.0, f1=0.8, p=1.0, r=1.0, n_pred=3, tp=3, fp=0, fn=0, topic=8, turns=5), "reward": 1.0},
        {**_reward(ndcg=0.5, f1=0.4, p=0.5, r=0.4, n_pred=4, tp=2, fp=2, fn=3, topic=27, turns=10), "reward": 0.0},
        {**_reward(ndcg=1.0, f1=0.9, p=0.9, r=0.9, n_pred=10, tp=9, fp=1, fn=1, topic=45, turns=8), "reward": 1.0},
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rewards)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")

    assert out["success"] == 2
    assert out["n_passed"] == 2
    assert out["pass_rate"] == 0.6667
    assert out["n_trials"] == 3


def test_success_zero_when_no_passes(tmp_path: Path) -> None:
    rewards = [
        {**_reward(ndcg=0.4, f1=0.2, p=0.5, r=0.1, n_pred=2, tp=1, fp=1, fn=9, topic=8, turns=5), "reward": 0.0},
        {**_reward(ndcg=0.6, f1=0.3, p=0.5, r=0.2, n_pred=2, tp=1, fp=1, fn=4, topic=27, turns=5), "reward": 0.0},
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rewards)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out["success"] == 0
    assert out["pass_rate"] == 0.0


def pytest_round(value: float) -> float:
    return round(value, 4)
