"""Unit tests for the clinical_trial_matching harbor_evaluator (NDCG@10)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "scripts" / "clinical_trial_matching")
)

from harbor_evaluator import evaluate  # noqa: E402


def _qrels(path: Path, rows: list[tuple[int, str, int]]) -> None:
    path.write_text("\n".join(f"{t} 0 {n} {g}" for t, n, g in rows) + "\n")


def _run(path: Path, rows: list[tuple[int, str, int, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            f"{t} Q0 {n} {r} {s} test-run" for t, n, r, s in rows
        )
        + "\n"
    )


def test_perfect_ranking_yields_ndcg_10_one(tmp_path: Path) -> None:
    qrels = tmp_path / "qrels.txt"
    _qrels(
        qrels,
        [
            (8, "NCT_A", 2),
            (8, "NCT_B", 2),
            (8, "NCT_C", 2),
            (8, "NCT_D", 2),
            (8, "NCT_E", 2),
            (8, "NCT_F", 1),
        ],
    )
    sub = tmp_path / "submission" / "run.txt"
    _run(
        sub,
        [
            (8, "NCT_A", 1, 0.99),
            (8, "NCT_B", 2, 0.95),
            (8, "NCT_C", 3, 0.92),
            (8, "NCT_D", 4, 0.88),
            (8, "NCT_E", 5, 0.84),
            (8, "NCT_F", 6, 0.50),
        ],
    )
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    assert score == pytest.approx(1.0)
    payload = json.loads((log / "reward.json").read_text())
    # Flat scalars only (Harbor schema).
    for k, v in payload.items():
        assert isinstance(v, (int, float)), f"{k} is {type(v).__name__}"
    assert payload["reward"] == pytest.approx(payload["ndcg_cut_10"])
    assert payload["topic_id"] == 8


def test_empty_submission_yields_zero(tmp_path: Path) -> None:
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2)])
    sub = tmp_path / "submission" / "run.txt"
    sub.parent.mkdir()
    sub.write_text("")
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    assert score == 0.0
    # The reward.json must still be written (so the aggregator sees this trial).
    assert (log / "reward.json").exists()


def test_only_unjudged_at_top_yields_zero(tmp_path: Path) -> None:
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2), (8, "NCT_B", 2)])
    sub = tmp_path / "submission" / "run.txt"
    _run(
        sub,
        [
            (8, "NCT_X", 1, 0.99),
            (8, "NCT_Y", 2, 0.95),
            (8, "NCT_Z", 3, 0.92),
        ],
    )
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    assert score == 0.0


def test_excluded_partial_credit(tmp_path: Path) -> None:
    """Excluded (rel=1) gets partial credit (linear gain in trec_eval)."""
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 1)])
    sub = tmp_path / "submission" / "run.txt"
    _run(sub, [(8, "NCT_A", 1, 0.99)])
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    # IDCG@10 with only one rel=1 doc: 1/log2(2) = 1.0
    # DCG@10: 1/log2(2) = 1.0 → NDCG = 1.0
    assert score == pytest.approx(1.0)


def test_no_reward_txt_written(tmp_path: Path) -> None:
    """Harbor's verifier reads reward.txt before reward.json. We must NOT
    write reward.txt; otherwise the rich payload is masked.
    """
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2)])
    sub = tmp_path / "submission" / "run.txt"
    _run(sub, [(8, "NCT_A", 1, 0.99)])
    log = tmp_path / "logs"
    evaluate(sub, qrels, log)
    assert not (log / "reward.txt").exists()
