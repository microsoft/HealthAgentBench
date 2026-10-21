"""Harbor verifier for the MSK-CHORD PANC TTE_OS survival task."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as _ev

_METRIC_KEYS = (
    "coverage",
    "c_index",
    "cmae_years",
    "ibs",
    "n_expected",
    "n_submitted",
    "n_unexpected",
    "n_duplicate_ids",
    "n_parsed",
)


def _write_outputs(log_dir: Path, payload: dict[str, Any]) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "reward.txt").write_text(f"{float(payload['reward']):.6f}\n")
    (log_dir / "metrics.json").write_text(json.dumps(payload, indent=2) + "\n")


def _failure_payload(baselines: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "reward": 0.0,
        "coverage": 0.0,
        "c_index": None,
        "cmae_years": None,
        "ibs": None,
        "n_expected": 0,
        "n_submitted": 0,
        "n_unexpected": 0,
        "n_duplicate_ids": 0,
        "n_parsed": 0,
    }
    payload.update(_baseline_fields(baselines))
    return payload


def _baseline_fields(baselines: dict[str, Any]) -> dict[str, float]:
    return {
        f"baseline_{model}_{metric}": float(baselines[model][metric])
        for model in ("cox", "rsf")
        for metric in ("c_index", "cmae_years", "ibs")
    }


def evaluate(
    submission_path: Path,
    test_labels_path: Path,
    train_outcomes_path: Path,
    baseline_path: Path,
    log_dir: Path,
    artifact_dir: Path,
) -> float:
    """Score one submission and write Harbor's reward and metric artifacts."""
    baselines = json.loads(baseline_path.read_text())
    try:
        metrics = _ev.score_submission(
            submission_path=submission_path,
            test_labels_path=test_labels_path,
            train_outcomes_path=train_outcomes_path,
        )
        result = _ev.evaluate_against_baselines(metrics, baselines)
        payload = {key: result[key] for key in _METRIC_KEYS}
        payload["reward"] = float(result["reward"])
        payload.update(
            {
                f"threshold_{name}": float(value)
                for name, value in result["thresholds"].items()
            }
        )
        payload.update(
            {f"passes_{name}": int(value) for name, value in result["passes"].items()}
        )
        payload.update(_baseline_fields(baselines))
    except Exception as exc:  # noqa: BLE001 - invalid agent output must score zero
        payload = _failure_payload(baselines)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "verifier_error.txt").write_text(
            f"{type(exc).__name__}: {exc}\n"
        )

    _write_outputs(log_dir, payload)
    return float(payload["reward"])
