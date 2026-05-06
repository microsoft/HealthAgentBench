# /// script
# dependencies = []
# ///
"""Harbor uv-script aggregator: pool per-trial mimic_iv_dq rewards.

Each per-trial ``reward.json`` (written by ``harbor_evaluator.evaluate``)
contains ``f1``, ``recall``, ``precision``, ``per_family_recall``,
``per_subtype_recall``, ``n_clusters``, ``n_clusters_caught``,
``n_flagged_rows``, ``n_useful_flagged_rows``, ``n_label_rows``,
``turn_count``.

Harbor concatenates all trial rewards into ``rewards.jsonl`` and passes
that file here. We compute:

- ``mean_f1`` / ``mean_recall`` / ``mean_precision``: simple per-trial mean
- ``micro_f1`` / ``micro_recall`` / ``micro_precision``: pooled across all
  clusters and flagged rows (treats every trial's clusters as part of one
  big set, so longer trials weigh more)
- ``mean_turn_count``: average agent turns per trial (nulls dropped)
- ``per_family_recall_macro``: mean per-family recall across trials
- ``per_subtype_recall_macro``: mean per-subtype recall across trials
- ``n_trials`` / ``n_clusters_total``

Usage (invoked by Harbor automatically via the ``metrics`` config):
    uv run scripts/mimic_iv_dq/aggregate_metric.py -i rewards.jsonl -o metric.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def _safe_div(num: float, den: float) -> float:
    return num / den if den > 0 else 0.0


def _parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        # Tolerate a bare scalar reward as a degenerate single-field record.
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
    files and return the parsed dicts. Harbor's ``rewards.jsonl`` only carries
    the scalar reward; for rich pooling we need the structured per-trial JSON.
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


def main(input_path: Path, output_path: Path) -> None:
    # Prefer reading per-trial reward.json files directly from the run dir
    # (where Harbor writes verifier/reward.json under each task subdir).
    # Fall back to the scalar rewards.jsonl that Harbor passes us.
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

    # Per-trial averages (macro)
    mean_f1 = sum(t.get("f1", t.get("reward", 0.0)) for t in trials) / n_trials
    mean_recall = sum(t.get("recall", 0.0) for t in trials) / n_trials
    mean_precision = sum(t.get("precision", 0.0) for t in trials) / n_trials

    # Pooled (micro): sum numerators and denominators across trials
    n_clusters_total = sum(t.get("n_clusters", 0) for t in trials)
    n_caught_total = sum(t.get("n_clusters_caught", 0) for t in trials)
    n_flagged_total = sum(t.get("n_flagged_rows", 0) for t in trials)
    n_useful_total = sum(t.get("n_useful_flagged_rows", 0) for t in trials)

    micro_recall = _safe_div(n_caught_total, n_clusters_total)
    micro_precision = _safe_div(n_useful_total, n_flagged_total)
    micro_f1 = _f1(micro_precision, micro_recall)

    # Per-family / per-subtype macro recall
    # Sources, in priority order:
    #   1. nested ``per_family_recall`` / ``per_subtype_recall`` dicts (rich
    #      reward.json payload with the legacy schema)
    #   2. flat ``fam_<family>`` / ``sub_<subtype>`` keys (current
    #      Harbor-compatible flat reward.json)
    fam_sums: dict[str, list[float]] = defaultdict(list)
    sub_sums: dict[str, list[float]] = defaultdict(list)
    for t in trials:
        nested_fam = t.get("per_family_recall", {}) or {}
        for k, v in nested_fam.items():
            try:
                fam_sums[k].append(float(v))
            except (TypeError, ValueError):
                pass
        nested_sub = t.get("per_subtype_recall", {}) or {}
        for k, v in nested_sub.items():
            try:
                sub_sums[k].append(float(v))
            except (TypeError, ValueError):
                pass
        if not nested_fam:
            for k, v in t.items():
                if isinstance(k, str) and k.startswith("fam_"):
                    try:
                        fam_sums[k[4:]].append(float(v))
                    except (TypeError, ValueError):
                        pass
        if not nested_sub:
            for k, v in t.items():
                if isinstance(k, str) and k.startswith("sub_"):
                    try:
                        sub_sums[k[4:]].append(float(v))
                    except (TypeError, ValueError):
                        pass
    per_family_recall_macro = {
        k: sum(vs) / len(vs) for k, vs in fam_sums.items() if vs
    }
    per_subtype_recall_macro = {
        k: sum(vs) / len(vs) for k, vs in sub_sums.items() if vs
    }

    # Turn-count mean (ignore nulls and the -1 sentinel that flat reward.json
    # uses to encode "missing" — Harbor's reward.json schema disallows None).
    turn_counts = [
        t.get("turn_count")
        for t in trials
        if t.get("turn_count") is not None and t.get("turn_count", -1) != -1
    ]
    mean_turn_count = (sum(turn_counts) / len(turn_counts)) if turn_counts else None

    result = {
        "mean_f1": round(mean_f1, 4),
        "mean_recall": round(mean_recall, 4),
        "mean_precision": round(mean_precision, 4),
        "micro_f1": round(micro_f1, 4),
        "micro_recall": round(micro_recall, 4),
        "micro_precision": round(micro_precision, 4),
        "per_family_recall_macro": {
            k: round(v, 4) for k, v in per_family_recall_macro.items()
        },
        "per_subtype_recall_macro": {
            k: round(v, 4) for k, v in per_subtype_recall_macro.items()
        },
        "mean_turn_count": (round(mean_turn_count, 2) if mean_turn_count is not None else None),
        "n_trials": n_trials,
        "n_clusters_total": n_clusters_total,
        "n_clusters_caught_total": n_caught_total,
        "n_flagged_rows_total": n_flagged_total,
        "n_useful_flagged_rows_total": n_useful_total,
    }
    output_path.write_text(json.dumps(result, indent=2))

    print(f"\n{'=' * 50}", file=sys.stderr)
    print(f" mimic_iv_dq aggregate ({n_trials} trials)", file=sys.stderr)
    print(f"  mean F1:        {result['mean_f1']:.4f}", file=sys.stderr)
    print(f"  mean recall:    {result['mean_recall']:.4f}", file=sys.stderr)
    print(f"  mean precision: {result['mean_precision']:.4f}", file=sys.stderr)
    print(f"  micro F1:       {result['micro_f1']:.4f}", file=sys.stderr)
    print(f"  clusters caught: {n_caught_total}/{n_clusters_total}", file=sys.stderr)
    if mean_turn_count is not None:
        print(f"  mean turns:     {result['mean_turn_count']}", file=sys.stderr)
    print(f"{'=' * 50}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
