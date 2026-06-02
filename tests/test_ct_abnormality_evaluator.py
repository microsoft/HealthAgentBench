"""Unit tests for the ct_abnormality harbor_evaluator.

The reward is **binary**: 1.0 iff every retained label matches gold,
0.0 otherwise. Per-volume diagnostic accuracy and per-label TP/FP/FN
are written to ``reward.json`` for the cross-volume aggregator.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "scripts" / "ct_abnormality")
)

from harbor_evaluator import evaluate  # noqa: E402


def _gold(path: Path, labels: list[tuple[str, int]]) -> None:
    payload = {
        "volume_name": "valid_TEST_a_1.nii.gz",
        "labels": [
            {"name": name, "gold": gold, "evidence": f"evidence-for-{name}"}
            for name, gold in labels
        ],
    }
    path.write_text(json.dumps(payload, indent=2))


def _submit(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def test_perfect_predictions_score_one(tmp_path: Path) -> None:
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0), ("Lung nodule", 1), ("Pleural effusion", 0)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Cardiomegaly: no", "Lung nodule: yes", "Pleural effusion: no"])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == pytest.approx(1.0)
    payload = json.loads((log / "reward.json").read_text())
    assert payload["reward"] == 1.0
    assert payload["accuracy"] == 1.0
    assert payload["n_correct"] == 3
    assert payload["n_retained"] == 3
    # No verifier_error.txt for clean submissions.
    assert not (log / "verifier_error.txt").exists()


def test_single_label_miss_collapses_reward_to_zero(tmp_path: Path) -> None:
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0), ("Lung nodule", 1)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Cardiomegaly: no", "Lung nodule: no"])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == 0.0
    payload = json.loads((log / "reward.json").read_text())
    assert payload["reward"] == 0.0
    assert payload["accuracy"] == 0.5
    assert payload["n_correct"] == 1
    assert payload["n_false_negatives"] == 1


def test_case_insensitive_label_match(tmp_path: Path) -> None:
    gold = tmp_path / "gold.json"
    _gold(gold, [("Lung nodule", 1)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["lung nodule: YES"])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == pytest.approx(1.0)


def test_tolerates_blank_lines_and_comments(tmp_path: Path) -> None:
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0), ("Lung nodule", 1)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(
        sub,
        [
            "# this is a comment",
            "",
            "Cardiomegaly: no",
            "Lung nodule: yes",
            "# trailing comment",
        ],
    )
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == pytest.approx(1.0)


def test_accepts_numeric_and_synonym_tokens(tmp_path: Path) -> None:
    gold = tmp_path / "gold.json"
    _gold(gold, [("A", 1), ("B", 0), ("C", 1), ("D", 0)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["A: 1", "B: 0", "C: true", "D: false"])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == pytest.approx(1.0)


def test_missing_submission_yields_zero(tmp_path: Path) -> None:
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0)])
    sub = tmp_path / "submission" / "predictions.txt"
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == 0.0
    assert (log / "verifier_error.txt").exists()


def test_present_but_empty_submission_yields_zero(tmp_path: Path) -> None:
    """A submission file that exists but carries no parseable predictions
    (only comments / blank lines) must score 0.0, not pass. The workspace
    shape looks plausible — the file is there — but the required artifact
    (real predictions) is effectively missing.
    """
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0), ("Lung nodule", 1)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["# I will fill this in later", "", "   "])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == 0.0
    assert (log / "verifier_error.txt").exists()


def test_missing_gold_yields_zero_not_crash(tmp_path: Path) -> None:
    """If the verifier's own gold.json was not staged, the verifier must fail
    closed (return 0.0 + verifier_error.txt) rather than raising — a missing
    setup artifact is a 0, never a launcher crash.
    """
    gold = tmp_path / "gold.json"  # never created
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Cardiomegaly: no"])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == 0.0
    assert (log / "verifier_error.txt").exists()


def test_missing_label_in_submission_counts_wrong(tmp_path: Path) -> None:
    """Labels present in gold but missing from the submission are scored wrong."""
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0), ("Lung nodule", 1)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Cardiomegaly: no"])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == 0.0
    reward = json.loads((log / "reward.json").read_text())
    assert reward["accuracy"] == 0.5
    # per_label lives in metrics.json (rich payload); reward.json is flat-scalar
    # only because Harbor's VerifierResult pydantic schema requires float|int.
    metrics = json.loads((log / "metrics.json").read_text())
    by_name = {pl["name"]: pl for pl in metrics["per_label"]}
    assert by_name["Lung nodule"]["predicted"] is None
    assert by_name["Lung nodule"]["match"] is False


def test_reward_json_is_flat_scalar_only(tmp_path: Path) -> None:
    """reward.json must contain only float|int values, no strings or
    nested structures, because Harbor's VerifierResult pydantic schema
    rejects anything else and crashes the launcher.
    """
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0), ("Lung nodule", 1)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Cardiomegaly: no", "Lung nodule: yes"])
    log = tmp_path / "logs"
    evaluate(sub, gold, log)
    reward = json.loads((log / "reward.json").read_text())
    for k, v in reward.items():
        assert isinstance(v, (int, float)), f"reward.json[{k!r}] is {type(v).__name__}, expected int/float"
    # The rich keys must NOT be in reward.json.
    assert "per_label" not in reward
    assert "volume_name" not in reward
    # But they must be in metrics.json.
    metrics = json.loads((log / "metrics.json").read_text())
    assert "per_label" in metrics
    assert "volume_name" in metrics


def test_reward_json_carries_flat_per_disease_keys(tmp_path: Path) -> None:
    """reward.json must carry flat gold_<suffix>/pred_<suffix> int keys so the
    aggregator can rebuild per-disease F1 from the flat reward stream Harbor
    feeds its uv-script metric (which never includes per_label).
    """
    gold = tmp_path / "gold.json"
    _gold(gold, [("Lung opacity", 1), ("Cardiomegaly", 0)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Lung opacity: yes"])  # Cardiomegaly omitted -> missing
    log = tmp_path / "logs"
    evaluate(sub, gold, log)
    reward = json.loads((log / "reward.json").read_text())
    assert reward["gold_lung_opacity"] == 1
    assert reward["pred_lung_opacity"] == 1
    assert reward["gold_cardiomegaly"] == 0
    assert reward["pred_cardiomegaly"] == -1  # missing prediction encoded as -1
    # Still flat-scalar only (Harbor VerifierResult schema).
    for k, v in reward.items():
        assert isinstance(v, (int, float)), f"{k} is {type(v).__name__}"


def test_unknown_labels_in_submission_are_ignored(tmp_path: Path) -> None:
    """Labels present in submission but not in gold do not affect the score."""
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Cardiomegaly: no", "Some unrelated finding: yes"])
    log = tmp_path / "logs"
    score = evaluate(sub, gold, log)
    assert score == pytest.approx(1.0)


def test_no_reward_txt_written(tmp_path: Path) -> None:
    """Harbor reads reward.txt first if present and would mask reward.json."""
    gold = tmp_path / "gold.json"
    _gold(gold, [("Cardiomegaly", 0)])
    sub = tmp_path / "submission" / "predictions.txt"
    _submit(sub, ["Cardiomegaly: no"])
    log = tmp_path / "logs"
    evaluate(sub, gold, log)
    assert not (log / "reward.txt").exists()
