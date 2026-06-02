# /// script
# dependencies = []
# ///
"""Harbor uv-script aggregator for the ct_abnormality benchmark.

Each per-trial ``reward.json`` (written by ``harbor_evaluator.evaluate``)
contains the binary ``reward`` (1.0 iff every retained label was correct,
0.0 otherwise), per-volume ``accuracy``, and ``per_label`` predictions.
Harbor concatenates all trial rewards into ``rewards.jsonl`` and passes
that file here.

We compute pass-rate, integer pass count (`success`), per-disease F1
across the volumes that retained that disease, plus macro and micro F1.

Per-disease F1 counts only the volumes whose gold included that disease;
volumes that did not retain it (because the radiology report did not
explicitly mention it) do not contribute to TP/FP/FN. This matches the
contract documented in ``.agent/plans/ct_abnormality.md``.

Usage (invoked by Harbor automatically via the ``metrics`` config):
    uv run scripts/ct_abnormality/aggregate_metric.py -i rewards.jsonl -o metric.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path


def _failed_trial_row() -> dict:
    """Synthetic zero-reward payload for a trial that crashed before the
    verifier ran (no reward.json). It counts against the denominator (pass
    rate, n_trials, mean accuracy) but contributes nothing to per-disease
    confusion — a crashed trial made no predictions.
    """
    return {"reward": 0.0, "accuracy": 0.0, "n_retained": 0, "n_correct": 0}


def _scan_trial_payloads(run_dir: Path) -> list[dict]:
    """Load per-trial payloads, preferring metrics.json (which carries the
    per-label breakdown) over reward.json (flat-scalar only because Harbor's
    VerifierResult schema rejects nested structures). Falls back to
    reward.json if metrics.json is absent.

    Trials that crashed before the verifier ran (an ``exception.txt`` or a
    per-trial ``result.json`` but no usable ``reward.json``) are folded in as
    synthetic zero-reward rows so they still count against the pass rate.
    """
    trials: list[dict] = []
    handled: set[str] = set()
    for trial_dir in sorted(run_dir.glob("*/verifier")):
        parent = trial_dir.parent
        metrics_path = trial_dir / "metrics.json"
        reward_path = trial_dir / "reward.json"
        path = metrics_path if metrics_path.exists() else reward_path
        if not path.exists():
            continue
        try:
            obj = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(obj, dict):
            trials.append(obj)
            handled.add(parent.name)
    # Synthesize zero rows for crashed trial dirs the loop above didn't cover.
    for trial_dir in sorted(p for p in run_dir.glob("*") if p.is_dir()):
        if trial_dir.name in handled:
            continue
        if (trial_dir / "exception.txt").exists() or (trial_dir / "result.json").exists():
            trials.append(_failed_trial_row())
    return trials


# Backwards-compatible alias for any existing callers that imported the
# old name. Prefer _scan_trial_payloads for new code.
_scan_reward_jsons = _scan_trial_payloads


def _parse_jsonl(path: Path) -> list[dict]:
    """Parse Harbor's ``rewards.jsonl``.

    Harbor writes one line per trial and a literal ``null`` for any trial that
    crashed before the verifier produced a reward (see
    ``harbor/metrics/uv_script.py`` and ``job.py`` appending ``None``). Those
    ``null`` lines are folded in as synthetic zero-reward rows so crashed trials
    count against the denominator instead of being silently dropped.
    """
    out: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj is None:
            out.append(_failed_trial_row())
        elif isinstance(obj, dict):
            out.append(obj)
    return out


def _safe_mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _f1(tp: int, fp: int, fn: int) -> float:
    denom = 2 * tp + fp + fn
    return (2 * tp / denom) if denom > 0 else 0.0


def _sanitize(name: str) -> str:
    """Convert a disease label to a metric-key suffix.

    Lower-case, alphanumeric + underscore only.
    """
    s = name.lower().replace("/", " ").replace("-", " ")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _accumulate(entry: dict[str, int], gold: int, pred: int | None) -> None:
    """Add one (gold, pred) observation to a disease confusion bucket.

    ``pred`` is ``None`` (or negative) for a missing/unparseable prediction,
    which counts as wrong on the side opposite to gold.
    """
    entry["n"] += 1
    if pred is None or pred < 0:
        if gold == 1:
            entry["fn"] += 1
        else:
            entry["fp"] += 1
    elif pred == 1 and gold == 1:
        entry["tp"] += 1
    elif pred == 1 and gold == 0:
        entry["fp"] += 1
    elif pred == 0 and gold == 0:
        entry["tn"] += 1
    else:
        entry["fn"] += 1


def _new_bucket() -> dict[str, int]:
    return {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "n": 0}


def _disease_confusion(trials: list[dict]) -> dict[str, dict[str, int]]:
    """Per-disease confusion keyed by sanitized suffix, across all trials.

    Two trial shapes are supported, in priority order:

    1. ``per_label`` list (present when the aggregator can read the rich
       ``metrics.json`` — e.g. run manually against the run root).
    2. flat ``gold_<suffix>`` / ``pred_<suffix>`` int keys (always present in
       ``reward.json``). This is the path that works through Harbor's uv-script
       metric hook, which feeds the aggregator only the flat reward stream.

    A disease only contributes for the volumes (trials) that retained it, so a
    volume whose report never mentioned a disease does not affect its F1.
    """
    by_label: dict[str, dict[str, int]] = {}
    for t in trials:
        per_label = t.get("per_label")
        if per_label:
            for pl in per_label:
                suffix = _sanitize(str(pl.get("name", "")))
                if not suffix:
                    continue
                pred = pl.get("predicted")
                _accumulate(
                    by_label.setdefault(suffix, _new_bucket()),
                    int(pl.get("gold", 0)),
                    None if pred is None else int(pred),
                )
            continue
        # Flat-key fallback: reconstruct from gold_<suffix> / pred_<suffix>.
        for key, gold_val in t.items():
            if not isinstance(key, str) or not key.startswith("gold_"):
                continue
            suffix = key[len("gold_") :]
            if not suffix:
                continue
            pred_raw = t.get(f"pred_{suffix}")
            pred = None if pred_raw is None else int(pred_raw)
            _accumulate(by_label.setdefault(suffix, _new_bucket()), int(gold_val), pred)
    return by_label


def main(input_path: Path, output_path: Path) -> None:
    trials: list[dict] = _scan_reward_jsons(input_path.parent)
    if not trials:
        trials = _parse_jsonl(input_path)
    if not trials:
        output_path.write_text(json.dumps({"error": "no rewards"}))
        return

    n_trials = len(trials)
    rewards = [float(t.get("reward", 0.0)) for t in trials]
    accuracies = [float(t.get("accuracy", 0.0)) for t in trials]
    successes = [1 if r >= 1.0 else 0 for r in rewards]

    # Per-disease confusion matrix across the volumes that retained the disease.
    by_label = _disease_confusion(trials)

    # Per-label F1 / precision / recall (only over labels with ≥1 retained pair).
    per_label_f1: dict[str, float] = {}
    per_label_p: dict[str, float] = {}
    per_label_r: dict[str, float] = {}
    sum_tp = sum_fp = sum_fn = 0
    for name, c in by_label.items():
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        sum_tp += tp
        sum_fp += fp
        sum_fn += fn
        per_label_f1[name] = _f1(tp, fp, fn)
        per_label_p[name] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        per_label_r[name] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    macro_f1 = _safe_mean(list(per_label_f1.values()))
    micro_f1 = _f1(sum_tp, sum_fp, sum_fn)

    result: dict[str, float | int] = {
        "success": sum(successes),
        "pass_rate": round(_safe_mean(successes), 4),
        "n_trials": n_trials,
        "mean_accuracy": round(_safe_mean(accuracies), 4),
        "macro_f1": round(macro_f1, 4),
        "micro_f1": round(micro_f1, 4),
        "n_total_true_positives": sum_tp,
        "n_total_false_positives": sum_fp,
        "n_total_false_negatives": sum_fn,
    }
    for name in sorted(by_label):
        suffix = _sanitize(name)
        c = by_label[name]
        result[f"f1_{suffix}"] = round(per_label_f1[name], 4)
        result[f"precision_{suffix}"] = round(per_label_p[name], 4)
        result[f"recall_{suffix}"] = round(per_label_r[name], 4)
        result[f"n_evaluated_{suffix}"] = int(c["n"])

    output_path.write_text(json.dumps(result, indent=2))

    print(f"\n{'=' * 50}", file=sys.stderr)
    print(
        f" ct_abnormality aggregate ({n_trials} trials)",
        file=sys.stderr,
    )
    print(
        f"  pass rate:    {result['pass_rate']:.4f}  ({result['success']}/{n_trials})",
        file=sys.stderr,
    )
    print(f"  mean acc:     {result['mean_accuracy']:.4f}", file=sys.stderr)
    print(f"  macro F1:     {result['macro_f1']:.4f}", file=sys.stderr)
    print(f"  micro F1:     {result['micro_f1']:.4f}", file=sys.stderr)
    print(f"{'=' * 50}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
