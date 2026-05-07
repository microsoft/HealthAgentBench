"""Unit tests for the clinical_trial_matching harbor_evaluator.

The reward is **NDCG@10** (linear gain, log2(i+1) discount). Diagnostic
set-based metrics (precision / recall / F1 against grade=2) are also
emitted in ``reward.json`` but do not influence the reward.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "scripts" / "clinical_trial_matching")
)

from harbor_evaluator import evaluate  # noqa: E402


def _qrels(path: Path, rows: list[tuple[int, str, int]]) -> None:
    path.write_text("\n".join(f"{t} 0 {n} {g}" for t, n, g in rows) + "\n")


def _submission(path: Path, ncts: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(ncts) + "\n")


def _dcg(grades: list[int]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(grades))


def test_ideal_ranking_yields_ndcg_one(tmp_path: Path) -> None:
    """Submitting trials in the ideal order — eligibles first, then the
    excluded — yields NDCG@10 == 1.0 by construction.
    """
    qrels = tmp_path / "qrels.txt"
    _qrels(
        qrels,
        [
            (8, "NCT_A", 2),
            (8, "NCT_B", 2),
            (8, "NCT_C", 2),
            (8, "NCT_D", 1),
            (8, "NCT_E", 0),
        ],
    )
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_A", "NCT_B", "NCT_C", "NCT_D", "NCT_E"])
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    assert score == pytest.approx(1.0)
    payload = json.loads((log / "reward.json").read_text())
    assert payload["reward"] == pytest.approx(1.0)
    assert payload["ndcg_at_10"] == pytest.approx(1.0)
    # Diagnostic set metrics over the full ranking: 3 TP / 5 predicted.
    assert payload["precision"] == pytest.approx(3 / 5)
    assert payload["recall"] == pytest.approx(1.0)
    assert payload["n_predicted"] == 5
    assert payload["n_eligible"] == 3
    assert payload["n_true_positives"] == 3
    assert payload["n_fp_excluded"] == 1
    assert payload["n_fp_nonrelevant"] == 1


def test_only_eligibles_submitted_lowers_ndcg_below_one(tmp_path: Path) -> None:
    """Submitting only the grade=2 trials forfeits the partial-credit
    grade=1 contribution that the ideal ranking includes.
    """
    qrels = tmp_path / "qrels.txt"
    _qrels(
        qrels,
        [
            (8, "NCT_A", 2),
            (8, "NCT_B", 2),
            (8, "NCT_C", 2),
            (8, "NCT_D", 1),
            (8, "NCT_E", 0),
        ],
    )
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_A", "NCT_B", "NCT_C"])
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    dcg = _dcg([2, 2, 2])
    idcg = _dcg([2, 2, 2, 1, 0])
    expected = dcg / idcg
    assert score == pytest.approx(expected)
    payload = json.loads((log / "reward.json").read_text())
    # F1 diagnostic is still 1.0 — perfect set match against grade=2.
    assert payload["f1"] == pytest.approx(1.0)


def test_misordered_eligibles_lower_ndcg(tmp_path: Path) -> None:
    """Putting an excluded (grade=1) trial above an eligible (grade=2)
    one moves gain into a deeper rank position, lowering NDCG@10.
    """
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2), (8, "NCT_B", 1), (8, "NCT_C", 2)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_B", "NCT_A", "NCT_C"])  # 1, 2, 2
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    dcg = _dcg([1, 2, 2])
    idcg = _dcg([2, 2, 1])
    assert score == pytest.approx(dcg / idcg)
    assert score < 1.0


def test_unjudged_predictions_contribute_zero_gain(tmp_path: Path) -> None:
    """Non-judged NCTs the agent submits get grade 0 (no DCG gain) and
    count as false positives in the diagnostic set metrics.
    """
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_A", "NCT_FAKE"])
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    payload = json.loads((log / "reward.json").read_text())
    assert score == pytest.approx(1.0)  # ideal order
    assert payload["precision"] == pytest.approx(0.5)
    assert payload["recall"] == pytest.approx(1.0)
    assert payload["n_fp_unjudged"] == 1


def test_empty_submission_yields_zero(tmp_path: Path) -> None:
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    sub.parent.mkdir()
    sub.write_text("")
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    assert score == 0.0
    payload = json.loads((log / "reward.json").read_text())
    assert payload["f1"] == 0.0
    assert payload["n_predicted"] == 0


def test_top_k_only_counts_for_ndcg(tmp_path: Path) -> None:
    """Eligible trials ranked beyond position 10 do not contribute to
    DCG@10 — only the top 10 ranks matter.
    """
    qrels = tmp_path / "qrels.txt"
    rows = [(8, f"NCT_PAD_{i}", 0) for i in range(10)]
    rows.append((8, "NCT_LATE", 2))
    _qrels(qrels, rows)
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, [f"NCT_PAD_{i}" for i in range(10)] + ["NCT_LATE"])
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    # NCT_LATE is at rank 11 → outside top-10 → DCG@10 = 0 → NDCG@10 = 0.
    assert score == 0.0
    payload = json.loads((log / "reward.json").read_text())
    # F1 diagnostic still picks up the eligible: 1 TP / 11 predicted.
    assert payload["recall"] == pytest.approx(1.0)
    assert payload["n_true_positives"] == 1


def test_handles_messy_submission_format(tmp_path: Path) -> None:
    """Tolerate blank lines, comments, CSV padding, whitespace."""
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2), (8, "NCT_B", 2)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    sub.parent.mkdir()
    sub.write_text("# comment\nNCT_A,0.99\n\nNCT_B  some_other_col\n# trailing\n")
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    assert score == pytest.approx(1.0)


def test_reward_is_binary_pass(tmp_path: Path) -> None:
    """Reward in reward.json is 1.0 iff NDCG@10 == 1.0; otherwise 0.0.
    This is what the launcher reads to compute the Successes column.
    """
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2), (8, "NCT_B", 1), (8, "NCT_C", 0)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_A", "NCT_B", "NCT_C"])  # ideal -> ndcg=1.0
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    payload = json.loads((log / "reward.json").read_text())
    assert score == pytest.approx(1.0)
    assert payload["reward"] == 1.0
    assert payload["ndcg_at_10"] == pytest.approx(1.0)


def test_reward_is_binary_fail_when_ndcg_below_one(tmp_path: Path) -> None:
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2), (8, "NCT_B", 2), (8, "NCT_C", 0)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_C", "NCT_A", "NCT_B"])  # bad order -> ndcg<1
    log = tmp_path / "logs"
    score = evaluate(sub, qrels, log)
    payload = json.loads((log / "reward.json").read_text())
    assert score < 1.0
    assert payload["reward"] == 0.0
    assert payload["ndcg_at_10"] < 1.0


def test_success_not_in_per_trial_reward_json(tmp_path: Path) -> None:
    """Per-trial reward.json must NOT have a `success` field. The launcher
    falls back to the aggregate metric (where `success` is an integer
    pass count) when this key is absent.
    """
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_A"])
    log = tmp_path / "logs"
    evaluate(sub, qrels, log)
    payload = json.loads((log / "reward.json").read_text())
    assert "success" not in payload


def test_no_reward_txt_written(tmp_path: Path) -> None:
    qrels = tmp_path / "qrels.txt"
    _qrels(qrels, [(8, "NCT_A", 2)])
    sub = tmp_path / "submission" / "ranked_trials.txt"
    _submission(sub, ["NCT_A"])
    log = tmp_path / "logs"
    evaluate(sub, qrels, log)
    assert not (log / "reward.txt").exists()
