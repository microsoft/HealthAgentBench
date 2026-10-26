"""Per-task trial-side verifier.

Runs inside the agent container under /tests/. The bootstrap service
derived test_labels.csv from the bundle at run time and wrote it to
/tests/test_labels.csv (RW-bind to host tasks/<task>/tests/ during
bootstrap; main does NOT have /tests/ mounted at agent runtime, so the
agent cannot read these labels during their work). The file is git-
ignored so it never enters version control. We compare the agent's
submission to those labels and write AUROC, AUPRC, and Brier to
/logs/verifier/metrics.json, and the binary reward to /logs/verifier/reward.txt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# evaluate.py ships alongside this file in tests/, which is baked into Harbor's
# separate verifier image (tests/Dockerfile), so it is never in the agent's reach.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as _ev  # noqa: E402


def evaluate(
    submission_path: Path,
    test_labels_path: Path,
    baseline_path: Path,
    log_dir: Path,
) -> float:
    log_dir.mkdir(parents=True, exist_ok=True)
    baseline_meta = json.loads(baseline_path.read_text())
    task_id = baseline_meta["task_id"]
    baseline_auroc = baseline_meta.get("baseline_auroc")

    result = _ev.score_submission(
        submission_path=submission_path,
        test_labels_path=test_labels_path,
        task_id=task_id,
        baseline_auroc=baseline_auroc,
    )

    # Reward is BINARY (1.0 = AUROC >= baseline - 0.01, 0.0 = did not). The
    # small 0.01 tolerance absorbs test-set sampling noise. This matches
    # the convention used by other Harbor benchmarks (e.g. ct_abnormality)
    # so the launcher's "Mean reward" column reports the pass rate and
    # "Successes" reports the pass count. The actual continuous AUROC is
    # carried separately as `auroc` and can be requested via
    # --metric-to-report auroc.
    #
    # Harbor's VerifierResult schema requires float | int values; only the
    # binary reward is written to reward.txt, with full metrics in metrics.json.
    success_int = int(bool(result.passed)) if result.passed is not None else 0
    # NOTE: do not emit per-trial ``success`` — the launcher's ``_resolve_metric``
    # prefers per-trial values when present, which would render ``success`` as the
    # rate (mean of 0/1) instead of the count. ct_abnormality follows the same
    # pattern; the aggregator below derives count from ``reward``.
    reward_payload: dict[str, float | int] = {
        "reward": float(success_int),
        "auroc": float(result.auroc),
        "auprc": float(result.auprc),
        "brier": float(result.brier),
        "n_test": int(result.n_test),
        "baseline_auroc": float(baseline_auroc) if baseline_auroc is not None else -1.0,
    }
    metrics_payload = dict(reward_payload)
    metrics_payload["task_id"] = task_id
    (log_dir / "reward.txt").write_text(f"{float(reward_payload['reward']):.6f}\n")
    (log_dir / "metrics.json").write_text(json.dumps(metrics_payload, indent=2))
    return float(result.auroc)
