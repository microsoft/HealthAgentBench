"""Smoke tests for scripts/ct_abnormality/aggregate_metric.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGG = REPO_ROOT / "scripts" / "ct_abnormality" / "aggregate_metric.py"


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


def _trial(reward: float, per_label: list[tuple[str, int, int]]) -> dict:
    """Build a per-trial reward.json-like dict.

    `per_label` items are (name, gold, predicted). Predicted may be -1 to denote
    "missing prediction" — the aggregator treats that as None.
    """
    pl = []
    for name, gold, pred in per_label:
        item = {"name": name, "gold": gold, "predicted": (None if pred == -1 else pred)}
        item["match"] = (pred == gold)
        pl.append(item)
    n_retained = len(per_label)
    n_correct = sum(1 for _, g, p in per_label if g == p)
    return {
        "reward": reward,
        "accuracy": n_correct / n_retained if n_retained else 0.0,
        "n_retained": n_retained,
        "n_correct": n_correct,
        "per_label": pl,
        "volume_name": "valid_TEST.nii.gz",
    }


def test_pass_rate_and_success_count(tmp_path: Path) -> None:
    rows = [
        _trial(1.0, [("Cardiomegaly", 0, 0), ("Lung nodule", 1, 1)]),
        _trial(0.0, [("Cardiomegaly", 0, 0), ("Lung nodule", 1, 0)]),
        _trial(1.0, [("Cardiomegaly", 1, 1), ("Lung nodule", 1, 1)]),
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rows)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")

    assert out["success"] == 2
    assert out["pass_rate"] == 0.6667
    assert out["n_trials"] == 3


def test_zero_pass_aggregate(tmp_path: Path) -> None:
    rows = [
        _trial(0.0, [("Cardiomegaly", 0, 1)]),
        _trial(0.0, [("Lung nodule", 1, 0)]),
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rows)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out["success"] == 0
    assert out["pass_rate"] == 0.0


def test_per_disease_f1_only_counts_retained_volumes(tmp_path: Path) -> None:
    """Each disease's F1 is computed only over the volumes that retained it.

    Trial A retains Lung nodule (gold=1, predicted=1) → TP for Lung nodule.
    Trial B retains Lung nodule (gold=0, predicted=1) → FP for Lung nodule.
    Trial C does NOT retain Lung nodule (its per_label has no Lung nodule
    entry). The aggregator must not charge Trial C for any TP/FP/FN of the
    Lung nodule label.
    """
    rows = [
        _trial(1.0, [("Lung nodule", 1, 1)]),
        _trial(0.0, [("Lung nodule", 0, 1)]),
        _trial(1.0, [("Cardiomegaly", 0, 0)]),
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rows)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")

    # Lung nodule: TP=1, FP=1, FN=0  → precision 0.5, recall 1.0, F1 = 2/(2+1) = 0.6667
    assert out["f1_lung_nodule"] == 0.6667
    assert out["precision_lung_nodule"] == 0.5
    assert out["recall_lung_nodule"] == 1.0
    assert out["n_evaluated_lung_nodule"] == 2
    # Cardiomegaly: TN only — TP=FP=FN=0 → F1 defined as 0
    assert out["f1_cardiomegaly"] == 0.0
    assert out["n_evaluated_cardiomegaly"] == 1


def test_missing_prediction_counted_as_wrong(tmp_path: Path) -> None:
    """A missing prediction (predicted=None) is wrong on either side of gold."""
    rows = [
        # Gold positive, no prediction → counts as FN.
        _trial(0.0, [("Lung nodule", 1, -1)]),
        # Gold negative, no prediction → counts as FP per aggregator semantics.
        _trial(0.0, [("Lung nodule", 0, -1)]),
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rows)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    # F1 with TP=0 → 0
    assert out["f1_lung_nodule"] == 0.0
    assert out["n_evaluated_lung_nodule"] == 2


def _flat_trial(reward: float, per_label: list[tuple[str, int, int]]) -> dict:
    """Build a per-trial dict shaped like the REAL flat reward.json.

    No ``per_label`` list (Harbor's uv-script metric never feeds it); instead the
    per-disease signal is carried as flat ``gold_<suffix>`` / ``pred_<suffix>``
    int keys. ``pred == -1`` denotes a missing prediction.
    """
    import re

    def sanitize(name: str) -> str:
        s = name.lower().replace("/", " ").replace("-", " ")
        return re.sub(r"[^a-z0-9]+", "_", s).strip("_")

    n_retained = len(per_label)
    n_correct = sum(1 for _, g, p in per_label if g == p)
    row: dict = {
        "reward": reward,
        "accuracy": n_correct / n_retained if n_retained else 0.0,
        "n_retained": n_retained,
        "n_correct": n_correct,
    }
    for name, gold, pred in per_label:
        s = sanitize(name)
        row[f"gold_{s}"] = gold
        row[f"pred_{s}"] = pred  # -1 already means "missing"
    return row


def test_per_disease_f1_from_flat_keys_only(tmp_path: Path) -> None:
    """The real Harbor path: reward.json carries flat gold_/pred_ keys and NO
    per_label. The aggregator must still reconstruct per-disease/macro/micro F1.

    This is the regression guard for the bug where Harbor's uv-script metric
    fed only the flat reward stream, so per_label was never available and all
    F1 collapsed to 0.0.
    """
    rows = [
        _flat_trial(1.0, [("Lung opacity", 1, 1)]),     # TP for lung_opacity
        _flat_trial(0.0, [("Cardiomegaly", 0, 1)]),     # FP for cardiomegaly
        _flat_trial(1.0, [("Cardiomegaly", 0, 0)]),     # TN for cardiomegaly
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rows)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")

    # lung_opacity: TP=1 → F1 1.0
    assert out["f1_lung_opacity"] == 1.0
    assert out["n_evaluated_lung_opacity"] == 1
    # cardiomegaly: TP=0, FP=1, FN=0 → F1 0.0, evaluated over the 2 volumes that retained it
    assert out["f1_cardiomegaly"] == 0.0
    assert out["n_evaluated_cardiomegaly"] == 2
    # micro F1 over pooled TP=1, FP=1, FN=0 → 2/(2+1) = 0.6667; NOT 0.0
    assert out["micro_f1"] == 0.6667
    # macro F1 = mean(1.0, 0.0) = 0.5
    assert out["macro_f1"] == 0.5


def test_flat_keys_missing_prediction_counted_wrong(tmp_path: Path) -> None:
    """pred=-1 in the flat keys is treated as wrong (same as per_label None)."""
    rows = [
        _flat_trial(0.0, [("Lung nodule", 1, -1)]),  # gold+ , missing → FN
        _flat_trial(0.0, [("Lung nodule", 0, -1)]),  # gold- , missing → FP
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rows)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out["f1_lung_nodule"] == 0.0
    assert out["n_evaluated_lung_nodule"] == 2


def test_crashed_trial_null_counts_against_denominator(tmp_path: Path) -> None:
    """Harbor writes a literal `null` line for a trial that crashed before the
    verifier ran. It must count as a zero-reward trial (denominator includes
    it), not be silently dropped — otherwise pass_rate is inflated.
    """
    # Two real passes + one crashed (null) trial.
    good = "\n".join(
        json.dumps(_flat_trial(1.0, [("Lung opacity", 1, 1)])) for _ in range(2)
    )
    (tmp_path / "rewards.jsonl").write_text(good + "\nnull\n")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")

    assert out["n_trials"] == 3          # crashed trial counted
    assert out["success"] == 2           # two passes
    assert out["pass_rate"] == 0.6667    # 2/3, NOT 2/2
    # Crashed trial contributes no per-disease confusion.
    assert out["f1_lung_opacity"] == 1.0
    assert out["n_evaluated_lung_opacity"] == 2


def test_empty_input(tmp_path: Path) -> None:
    (tmp_path / "rewards.jsonl").write_text("")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out == {"error": "no rewards"}
