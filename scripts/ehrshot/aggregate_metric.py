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
    """Load per-trial reward payloads, one row per trial subdirectory.

    Iterates every trial subdir under ``run_dir`` (anything matching the
    Harbor ``<task>__<random>`` shape with an ``exception.txt``, ``result.json``,
    or ``verifier/`` directory). For each trial:

    * If ``verifier/metrics.json`` or ``verifier/reward.json`` exists, load
      that payload as-is.
    * Otherwise the trial failed before scoring (agent timeout,
      ``NonZeroAgentExitCodeError``, verifier crash, etc.). Emit a synthetic
      zero-reward payload so the trial is counted in the denominator and
      contributes 0 to the pass count. Without this, "no submission" trials
      are silently excluded — which artificially inflates the pass rate and
      hides agent failures.
    """
    trials: list[dict] = []
    for trial_dir in sorted(run_dir.iterdir()):
        if not trial_dir.is_dir():
            continue
        name = trial_dir.name
        if "__" not in name:
            continue
        # Skip launcher/aggregator/orchestration top-level files.
        if name.startswith("."):
            continue
        verifier_dir = trial_dir / "verifier"
        metrics_path = verifier_dir / "metrics.json"
        reward_path = verifier_dir / "reward.json"
        path = metrics_path if metrics_path.exists() else (
            reward_path if reward_path.exists() else None
        )
        if path is not None:
            try:
                obj = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(obj, dict):
                trials.append(obj)
            continue
        # No verifier output. Count this attempt as a 0 only if there is
        # evidence the trial actually ran (result.json or exception.txt). We
        # deliberately exclude in-flight / placeholder dirs that have neither
        # so a partially-completed run-dir doesn't mark its still-running
        # trials as failures.
        result_path = trial_dir / "result.json"
        exception_path = trial_dir / "exception.txt"
        if not result_path.exists() and not exception_path.exists():
            continue
        task_id = name.split("__", 1)[0]
        trials.append(
            {
                "task_id": task_id,
                "reward": 0.0,
                "auroc": None,
                "auprc": None,
                "brier": None,
                "n_test": None,
                "baseline_auroc": None,
                "_failed": True,
            }
        )
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
    # Matches the ct_abnormality aggregator pattern. Failed trials contribute
    # ``reward=0.0`` via the synthetic payload in ``_scan_trial_payloads``.
    successes = [1 if r >= 1.0 else 0 for r in rewards]
    # Non-reward fields are only meaningful on trials that actually scored;
    # synthetic failure payloads carry None and must be filtered out.
    def _floats(key: str) -> list[float]:
        return [
            float(t[key]) for t in trials
            if key in t and t[key] is not None
        ]
    aurocs = _floats("auroc")
    auprcs = _floats("auprc")
    briers = _floats("brier")
    baselines = _floats("baseline_auroc")
    n_tests = [
        int(t["n_test"]) for t in trials
        if t.get("n_test") is not None
    ]
    n_failed = sum(1 for t in trials if t.get("_failed"))

    payload: dict[str, float | int | str] = {
        # Headline columns Harbor and the launcher use.
        "reward": _safe_mean(rewards),                 # = pass rate
        "success": int(sum(successes)),                # = pass count
        "n_trials": len(trials),
        "n_failed": int(n_failed),                     # trials with no submission
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
