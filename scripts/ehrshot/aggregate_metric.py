# /// script
# dependencies = []
# ///
"""Harbor uv-script aggregator for the ehrshot benchmark.

Each per-trial ``reward.json`` (written by the trial-side
``harbor_evaluator.evaluate``) is a flat ``dict[str, float | int]`` with
keys ``reward`` (binary 0/1 indicating whether the agent's AUROC beat
the count+gbm baseline), ``success`` (same as int), ``auroc``,
``auprc``, ``brier``, ``n_test``, and ``baseline_auroc``.

Harbor's default ``MeanReward`` metric rejects reward dicts with more
than one key, so every Harbor benchmark in this repo ships a
``scripts/<benchmark>/aggregate_metric.py`` that the launcher
auto-detects and registers as the trial-aggregation metric. This file
plays that role for ehrshot.

Output (written to ``-o``): a flat JSON dict with:
  * ``reward`` — pass rate (mean of per-trial ``reward``)
  * ``success`` — number of trials that passed (sum of per-trial ``success``)
  * ``n_trials`` — total trial count
  * ``mean_auroc`` / ``stdev_auroc`` — mean and sample stdev of agent AUROC
  * ``mean_auprc`` / ``stdev_auprc``
  * ``mean_brier`` / ``stdev_brier``
  * ``mean_baseline_auroc`` — mean of the count+gbm baseline gates
  * ``mean_n_test`` — mean test-cohort size across the sweep

Usage (Harbor invokes this automatically via the ``metrics`` config):

    uv run scripts/ehrshot/aggregate_metric.py -i rewards.jsonl -o metric.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def _scan_trial_payloads(run_dir: Path) -> list[dict]:
    """Load per-trial reward payloads. Prefer ``metrics.json`` (which carries
    the rich payload including ``task_id``) over ``reward.json`` (flat-scalar
    only because Harbor's VerifierResult schema rejects nested structures).
    """
    trials: list[dict] = []
    for verifier_dir in sorted(run_dir.glob("*/verifier")):
        metrics_path = verifier_dir / "metrics.json"
        reward_path = verifier_dir / "reward.json"
        path = metrics_path if metrics_path.exists() else reward_path
        if not path.exists():
            continue
        try:
            obj = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(obj, dict):
            trials.append(obj)
    return trials


def _parse_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _safe_mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _safe_stdev(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def main(input_path: Path, output_path: Path) -> None:
    # Harbor passes ``-i rewards.jsonl`` whose parent directory contains
    # the per-trial subdirs. Scan those first; fall back to the JSONL.
    trials: list[dict] = _scan_trial_payloads(input_path.parent)
    if not trials:
        trials = _parse_jsonl(input_path)
    if not trials:
        output_path.write_text(json.dumps({"error": "no rewards"}))
        return

    rewards = [float(t.get("reward", 0.0)) for t in trials]
    # Derive pass-count from ``reward`` rather than reading a per-trial
    # ``success`` field. Per-trial reward.json intentionally does not include
    # ``success`` (see HARBOR_EVALUATOR_STUB in generate_harbor_tasks.py) so
    # the launcher's ``_resolve_metric`` falls through to this aggregate
    # value and renders ``success`` as the integer pass count, not the mean.
    # Matches the ct_abnormality aggregator pattern.
    successes = [1 if r >= 1.0 else 0 for r in rewards]
    aurocs = [float(t["auroc"]) for t in trials if "auroc" in t]
    auprcs = [float(t["auprc"]) for t in trials if "auprc" in t]
    briers = [float(t["brier"]) for t in trials if "brier" in t]
    baselines = [float(t["baseline_auroc"]) for t in trials if "baseline_auroc" in t]
    n_tests = [int(t["n_test"]) for t in trials if "n_test" in t]

    payload: dict[str, float | int | str] = {
        # Headline columns Harbor and the launcher use.
        "reward": _safe_mean(rewards),                 # = pass rate
        "success": int(sum(successes)),                # = pass count
        "n_trials": len(trials),
        # Per-trial score distribution.
        "mean_auroc": _safe_mean(aurocs),
        "stdev_auroc": _safe_stdev(aurocs),
        "mean_auprc": _safe_mean(auprcs),
        "stdev_auprc": _safe_stdev(auprcs),
        "mean_brier": _safe_mean(briers),
        "stdev_brier": _safe_stdev(briers),
        # Sanity context.
        "mean_baseline_auroc": _safe_mean(baselines),
        "mean_n_test": _safe_mean([float(n) for n in n_tests]),
    }
    output_path.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.input, args.output)
