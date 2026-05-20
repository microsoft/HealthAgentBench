# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Harbor uv-script metric: pool per-trial CheXprompt rewards.

Each per-trial ``reward.json`` (written by ``verify_meta_task.py``)
carries the flat-scalar payload::

    {"reward": 0.0|1.0, "n_tasks": int, "n_pass": int, "pass_rate": float}

(``reward`` is 1 iff CheXprompt reported zero clinically-significant
errors for every row in the trial. For the curated 1-row-per-trial
layout, ``reward == pass_rate``.)

This script pools across trials and writes a single ``metric.json``::

    {
      "reward":  mean reward across trials                  (= pass rate),
      "success": integer count of trials that passed,
      "n_trials": total trials seen,
      "n_failed": trials with no submission / verifier error,
      "mean_pass_rate": mean per-trial pass_rate            (same as reward
                        in the 1-row layout; differs only when n_tasks > 1).
      "mean_sig_errors": mean clinically-significant errors per trial,
                         averaged across rows that had at least one
                         successful CheXprompt run (synthetic-zero
                         failures are excluded so the metric isn't
                         biased). Lower is better.
    }

The launcher's ``_resolve_metric`` prefers per-trial mean for ``reward``
and falls through to the aggregate count for ``success`` — same pattern
as the EHRSHOT / EHRSQL / ct_abnormality aggregators.

Failure semantics (mirrors ehrshot/ehrsql): a trial dir with
``exception.txt`` or ``result.json`` but **no** ``reward.json`` is
counted as a synthetic 0-reward row so AgentTimeoutError /
NonZeroAgentExitCode trials drop pass rate rather than being silently
excluded.

Usage (Harbor invokes this from the task's ``metrics`` config):

    uv run scripts/xray_report_gen/aggregate_metric.py \\
        -i rewards.jsonl -o metric.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def _scan_trial_payloads(run_dir: Path) -> list[dict[str, Any]]:
    """Yield one payload per trial subdir.

    Prefer metrics.json (richer) over reward.json (both share the flat
    scalars). For trial dirs without verifier output but with evidence
    the trial ran (result.json or exception.txt), emit a synthetic
    0-reward row so the aggregate denominator is honest about failures.
    """
    out: list[dict[str, Any]] = []
    if not run_dir.exists():
        return out
    for d in sorted(run_dir.iterdir()):
        if not d.is_dir() or "__" not in d.name or d.name.startswith("."):
            continue
        verifier_dir = d / "verifier"
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
                out.append(obj)
            continue
        # No verifier output but trial did run → synthetic failure.
        if (d / "result.json").exists() or (d / "exception.txt").exists():
            out.append({
                "reward": 0.0,
                "n_tasks": 0,
                "n_pass": 0,
                "pass_rate": 0.0,
                "_failed": True,
            })
    return out


def _parse_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
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


def main(input_path: Path, output_path: Path) -> None:
    trials = _scan_trial_payloads(input_path.parent)
    if not trials:
        trials = _parse_jsonl(input_path)
    if not trials:
        output_path.write_text(json.dumps({"error": "no rewards"}))
        return

    rewards = [float(t.get("reward", 0.0)) for t in trials]
    successes = [1 if r >= 1.0 else 0 for r in rewards]
    n_failed = sum(1 for t in trials if t.get("_failed"))
    pass_rates = [
        float(t["pass_rate"]) for t in trials if t.get("pass_rate") is not None
    ]
    # Diagnostic: average clinically-significant errors per trial.
    # Skip synthetic-zero failed trials so we don't bias the mean
    # downward — they didn't actually score 0 sig errors, they didn't
    # score at all. Pass-rate metric handles them separately.
    sig_errs = [
        float(t["mean_sig_errors"]) for t in trials
        if t.get("mean_sig_errors") is not None and not t.get("_failed")
    ]

    payload: dict[str, float | int] = {
        "reward": mean(rewards) if rewards else 0.0,
        "success": int(sum(successes)),
        "n_trials": len(trials),
        "n_failed": int(n_failed),
        "mean_pass_rate": mean(pass_rates) if pass_rates else 0.0,
        "mean_sig_errors": mean(sig_errs) if sig_errs else 0.0,
    }
    output_path.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.input, args.output)
