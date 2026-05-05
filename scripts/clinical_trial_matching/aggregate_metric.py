# /// script
# dependencies = []
# ///
"""Harbor uv-script aggregator for the clinical_trial_matching benchmark.

Each per-trial ``reward.json`` (written by ``harbor_evaluator.evaluate``)
contains ``f1``, ``precision``, ``recall``, plus diagnostic counts. Harbor
concatenates all trial rewards into ``rewards.jsonl`` and passes that file
here.

We compute mean / median across the 10 subtasks plus per-topic breakdowns
and pooled (micro) precision / recall / F1 from the summed counts.

Usage (invoked by Harbor automatically via the ``metrics`` config):
    uv run scripts/clinical_trial_matching/aggregate_metric.py \\
        -i rewards.jsonl -o metric.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def _parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        try:
            return {"reward": float(line)}
        except ValueError:
            return None
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, (int, float)):
        return {"reward": float(obj)}
    return None


def _scan_reward_jsons(run_dir: Path) -> list[dict]:
    trials: list[dict] = []
    for reward_path in sorted(run_dir.glob("*/verifier/reward.json")):
        try:
            obj = json.loads(reward_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(obj, dict):
            trials.append(obj)
    return trials


def _safe_mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _safe_median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def main(input_path: Path, output_path: Path) -> None:
    trials: list[dict] = _scan_reward_jsons(input_path.parent)
    if not trials:
        for line in input_path.read_text().splitlines():
            rec = _parse_line(line)
            if rec is not None:
                trials.append(rec)
    if not trials:
        output_path.write_text(json.dumps({"error": "no rewards"}))
        return

    n_trials = len(trials)
    ndcgs = [float(t.get("ndcg_at_10", t.get("reward", 0.0))) for t in trials]
    successes = [int(t.get("success", 1 if float(t.get("ndcg_at_10", 0.0)) >= 1.0 else 0)) for t in trials]
    dcgs = [float(t.get("dcg_at_10", 0.0)) for t in trials]
    p_at_10 = [float(t.get("precision_at_10", 0.0)) for t in trials]
    r_at_10 = [float(t.get("recall_at_10", 0.0)) for t in trials]
    f1s = [float(t.get("f1", 0.0)) for t in trials]
    precisions = [float(t.get("precision", 0.0)) for t in trials]
    recalls = [float(t.get("recall", 0.0)) for t in trials]
    turn_counts = [
        int(t["turn_count"])
        for t in trials
        if "turn_count" in t and t["turn_count"] not in (None, -1)
    ]

    # Pooled (micro): sum the numerators and denominators across trials.
    sum_tp = sum(int(t.get("n_true_positives", 0)) for t in trials)
    sum_fp = sum(int(t.get("n_false_positives", 0)) for t in trials)
    sum_fn = sum(int(t.get("n_false_negatives", 0)) for t in trials)
    micro_precision = sum_tp / (sum_tp + sum_fp) if (sum_tp + sum_fp) > 0 else 0.0
    micro_recall = sum_tp / (sum_tp + sum_fn) if (sum_tp + sum_fn) > 0 else 0.0
    micro_f1 = _f1(micro_precision, micro_recall)

    result: dict[str, float | int] = {
        "success": sum(successes),
        "pass_rate": round(_safe_mean(successes), 4),
        "n_passed": sum(successes),
        "mean_ndcg_at_10": round(_safe_mean(ndcgs), 4),
        "median_ndcg_at_10": round(_safe_median(ndcgs), 4),
        "mean_dcg_at_10": round(_safe_mean(dcgs), 4),
        "mean_precision_at_10": round(_safe_mean(p_at_10), 4),
        "mean_recall_at_10": round(_safe_mean(r_at_10), 4),
        "mean_f1": round(_safe_mean(f1s), 4),
        "median_f1": round(_safe_median(f1s), 4),
        "mean_precision": round(_safe_mean(precisions), 4),
        "mean_recall": round(_safe_mean(recalls), 4),
        "micro_precision": round(micro_precision, 4),
        "micro_recall": round(micro_recall, 4),
        "micro_f1": round(micro_f1, 4),
        "n_trials": n_trials,
        "n_total_predictions": int(sum(int(t.get("n_predicted", 0)) for t in trials)),
        "n_total_true_positives": sum_tp,
        "n_total_false_positives": sum_fp,
        "n_total_false_negatives": sum_fn,
    }
    if turn_counts:
        result["mean_turn_count"] = round(_safe_mean(turn_counts), 2)

    # Per-topic breakdown (mean across attempts for the same topic).
    by_topic: dict[int, list[float]] = {}
    by_topic_f1: dict[int, list[float]] = {}
    for t, ndcg, f1 in zip(trials, ndcgs, f1s):
        try:
            tid = int(t.get("topic_id", -1))
        except (TypeError, ValueError):
            continue
        if tid >= 0:
            by_topic.setdefault(tid, []).append(ndcg)
            by_topic_f1.setdefault(tid, []).append(f1)
    for tid in sorted(by_topic):
        result[f"topic_{tid}_mean_ndcg_at_10"] = round(_safe_mean(by_topic[tid]), 4)
        result[f"topic_{tid}_mean_f1"] = round(_safe_mean(by_topic_f1[tid]), 4)

    output_path.write_text(json.dumps(result, indent=2))

    print(f"\n{'=' * 50}", file=sys.stderr)
    print(f" clinical_trial_matching aggregate ({n_trials} trials)", file=sys.stderr)
    print(f"  pass rate:       {result['pass_rate']:.4f}  ({result['n_passed']}/{n_trials})", file=sys.stderr)
    print(f"  mean NDCG@10:    {result['mean_ndcg_at_10']:.4f}", file=sys.stderr)
    print(f"  mean P@10:       {result['mean_precision_at_10']:.4f}", file=sys.stderr)
    print(f"  mean R@10:       {result['mean_recall_at_10']:.4f}", file=sys.stderr)
    print(f"  mean F1 (full):  {result['mean_f1']:.4f}", file=sys.stderr)
    print(f"  micro F1 (full): {result['micro_f1']:.4f}", file=sys.stderr)
    print(f"{'=' * 50}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
