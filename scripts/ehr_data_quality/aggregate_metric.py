# /// script
# dependencies = []
# ///
"""Harbor uv-script aggregator: pool per-trial ehr_data_quality rewards.

Each per-trial ``reward.json`` (written by ``harbor_evaluator.evaluate``)
carries the flat-scalar payload::

    {"reward": 0.0|1.0, "n_tasks": 1, "n_pass": int, "pass_rate": float,
     "f1": ..., "recall": ..., "precision": ..., ...}

Pass criterion (binary): ``recall == 1.0 AND precision > 0.5``.

This script pools across trials and writes a single ``metric.json``::

    {
      "reward":  mean reward across trials                  (= pass rate),
      "success": integer count of trials that passed,
      "n_trials": total trials seen,
      "n_failed": trials with no submission / verifier error,
      "mean_pass_rate": same as reward in the 1-task layout,
      "mean_f1" / "mean_recall" / "mean_precision": per-trial diagnostics,
      "micro_f1" / "micro_recall" / "micro_precision": pooled diagnostics
          (treats every trial's clusters as part of one big set),
      "per_family_recall_macro" / "per_subtype_recall_macro": breakdowns,
      "mean_turn_count" / "n_clusters_total".
    }

Failure semantics (mirrors xray_report_gen): a trial dir with
``exception.txt`` or ``result.json`` but **no** ``reward.json`` is
counted as a synthetic 0-reward row so AgentTimeoutError /
NonZeroAgentExitCode trials drop the pass rate rather than being
silently excluded.

Usage (invoked by Harbor automatically via the ``metrics`` config):
    uv run scripts/ehr_data_quality/aggregate_metric.py -i rewards.jsonl -o metric.json
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
    files and return the parsed dicts. Synthesizes a 0-reward row for any
    trial dir that has ``exception.txt`` or ``result.json`` but no
    ``reward.json`` so timeouts and crashes count against the pass rate
    rather than being silently dropped.
    """
    trials: list[dict] = []
    if not run_dir.exists():
        return trials
    for trial_dir in sorted(run_dir.iterdir()):
        if not trial_dir.is_dir() or "__" not in trial_dir.name or trial_dir.name.startswith("."):
            continue
        reward_path = trial_dir / "verifier" / "reward.json"
        if reward_path.exists():
            try:
                obj = json.loads(reward_path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(obj, dict):
                trials.append(obj)
            continue
        # No verifier output but trial did run -> synthetic failure.
        if (trial_dir / "result.json").exists() or (trial_dir / "exception.txt").exists():
            trials.append({
                "reward": 0.0,
                "n_tasks": 1,
                "n_pass": 0,
                "pass_rate": 0.0,
                "f1": 0.0,
                "recall": 0.0,
                "precision": 0.0,
                "_failed": True,
            })
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

    # Headline pass-rate metrics (xray_report_gen convention).
    rewards = [float(t.get("reward", 0.0)) for t in trials]
    successes = [1 if r >= 1.0 else 0 for r in rewards]
    n_failed = sum(1 for t in trials if t.get("_failed"))

    # Per-trial averages (macro). F1 / recall / precision are kept as
    # diagnostics so they continue to show up alongside reward / success
    # in paper/baselines.md.
    mean_f1 = sum(t.get("f1", 0.0) for t in trials) / n_trials
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

    reward = sum(rewards) / n_trials if rewards else 0.0
    success = int(sum(successes))

    result = {
        # Headline metrics (xray_report_gen convention).
        "reward": round(reward, 4),
        "success": success,
        "n_trials": n_trials,
        "n_failed": int(n_failed),
        "mean_pass_rate": round(reward, 4),
        # F1 / recall / precision diagnostics — exposed at top level so they
        # surface in paper/baselines.md alongside reward and success.
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
        "n_clusters_total": n_clusters_total,
        "n_clusters_caught_total": n_caught_total,
        "n_flagged_rows_total": n_flagged_total,
        "n_useful_flagged_rows_total": n_useful_total,
    }
    output_path.write_text(json.dumps(result, indent=2))

    print(f"\n{'=' * 50}", file=sys.stderr)
    print(f" ehr_data_quality aggregate ({n_trials} trials, {n_failed} failed)", file=sys.stderr)
    print(f"  reward (pass rate): {result['reward']:.4f}", file=sys.stderr)
    print(f"  success:            {success}/{n_trials}", file=sys.stderr)
    print(f"  mean F1:            {result['mean_f1']:.4f}", file=sys.stderr)
    print(f"  mean recall:        {result['mean_recall']:.4f}", file=sys.stderr)
    print(f"  mean precision:     {result['mean_precision']:.4f}", file=sys.stderr)
    print(f"  micro F1:           {result['micro_f1']:.4f}", file=sys.stderr)
    print(f"  clusters caught:    {n_caught_total}/{n_clusters_total}", file=sys.stderr)
    if mean_turn_count is not None:
        print(f"  mean turns:         {result['mean_turn_count']}", file=sys.stderr)
    print(f"{'=' * 50}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
