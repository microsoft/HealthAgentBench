# /// script
# dependencies = []
# ///
"""Harbor uv-script aggregator for the clinical_trial_matching benchmark.

Each per-trial ``reward.json`` (written by ``harbor_evaluator.evaluate``)
contains ``ndcg_cut_10``, ``ndcg_cut_1000``, ``recall_1000``,
``n_judged_eligible/excluded/nonrelevant``, ``n_submission_rows``,
``topic_id``, and ``turn_count``. Harbor concatenates all trial rewards
into ``rewards.jsonl`` and passes that file here.

We compute simple mean / median across the 10 subtasks plus per-topic
breakdown so the multi-task run summary surfaces both.

Usage (invoked by Harbor automatically via the ``metrics`` config):
    uv run scripts/clinical_trial_matching/aggregate_metric.py -i rewards.jsonl -o metric.json
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
    """Scan a Harbor run directory for per-trial ``verifier/reward.json``
    files. Harbor's ``rewards.jsonl`` only carries the scalar reward; for
    rich pooling we need the structured per-trial JSON.
    """
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


def main(input_path: Path, output_path: Path) -> None:
    # Prefer reading per-trial reward.json files directly from the run dir
    # (rich payloads). Fall back to the scalar rewards.jsonl that Harbor
    # passes us.
    trials: list[dict] = _scan_reward_jsons(input_path.parent)
    if not trials:
        for line in input_path.read_text().splitlines():
            rec = _parse_line(line)
            if rec is None:
                continue
            trials.append(rec)
    if not trials:
        output_path.write_text(json.dumps({"error": "no rewards"}))
        return

    n_trials = len(trials)

    ndcg10s = [float(t.get("ndcg_cut_10", t.get("reward", 0.0))) for t in trials]
    ndcg1000s = [float(t.get("ndcg_cut_1000", 0.0)) for t in trials]
    recall1000s = [float(t.get("recall_1000", 0.0)) for t in trials]
    turn_counts = [
        int(t["turn_count"])
        for t in trials
        if "turn_count" in t and t["turn_count"] not in (None, -1)
    ]

    result: dict[str, float | int] = {
        "mean_ndcg_cut_10": round(_safe_mean(ndcg10s), 4),
        "median_ndcg_cut_10": round(_safe_median(ndcg10s), 4),
        "mean_ndcg_cut_1000": round(_safe_mean(ndcg1000s), 4),
        "mean_recall_1000": round(_safe_mean(recall1000s), 4),
        "n_trials": n_trials,
    }
    if turn_counts:
        result["mean_turn_count"] = round(_safe_mean(turn_counts), 2)

    # Per-topic NDCG@10. With ``n_attempts > 1`` the same topic appears
    # multiple times — average across attempts.
    by_topic: dict[int, list[float]] = {}
    for t, score in zip(trials, ndcg10s):
        try:
            tid = int(t.get("topic_id", -1))
        except (TypeError, ValueError):
            continue
        if tid >= 0:
            by_topic.setdefault(tid, []).append(score)
    for tid in sorted(by_topic):
        result[f"topic_{tid}_mean_ndcg_cut_10"] = round(_safe_mean(by_topic[tid]), 4)

    output_path.write_text(json.dumps(result, indent=2))

    print(f"\n{'=' * 50}", file=sys.stderr)
    print(f" clinical_trial_matching aggregate ({n_trials} trials)", file=sys.stderr)
    print(f"  mean NDCG@10:    {result['mean_ndcg_cut_10']:.4f}", file=sys.stderr)
    print(f"  median NDCG@10:  {result['median_ndcg_cut_10']:.4f}", file=sys.stderr)
    print(f"  mean NDCG@1000:  {result['mean_ndcg_cut_1000']:.4f}", file=sys.stderr)
    print(f"  mean recall@1000:{result['mean_recall_1000']:.4f}", file=sys.stderr)
    print(f"{'=' * 50}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
