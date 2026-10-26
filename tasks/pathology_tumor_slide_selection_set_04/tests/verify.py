#!/usr/bin/env python3
"""Verifier for pathology_tumor_slide_selection HealthAgentBench tasks.

Reward is 1.0 iff the submitted set of `tumor_slides` exactly matches the set
of slides whose hidden label is tumor, else 0.0. Slide-level precision, recall
and F1 are reported as diagnostics. Pure standard library; no dependencies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, default=Path("/workspace/submission.json"))
    parser.add_argument("--answer-key", type=Path, default=Path("/tests/task_answer_key.json"))
    parser.add_argument("--reward-txt", type=Path, default=Path("/logs/verifier/reward.txt"))
    parser.add_argument("--metrics-json", type=Path, default=Path("/logs/verifier/metrics.json"))
    parser.add_argument(
        "--error-analysis-file",
        type=Path,
        default=Path("/logs/artifacts/error_analysis.json"),
    )
    return parser.parse_args()


def _normalize_slide_name(value: Any) -> str | None:
    """Reduce a slide reference to its stem, e.g. '/data/slides/Slide_3.svs' -> 'slide_3'."""
    if not isinstance(value, str):
        return None
    stem = Path(value.strip()).name
    if stem.lower().endswith(".svs"):
        stem = stem[:-4]
    stem = stem.strip().lower()
    return stem or None


def _extract_prediction(payload: Any) -> tuple[set[str] | None, str | None]:
    """Return (predicted slide set, error). Accepts {"tumor_slides": [...]}, a bare
    list of names, a single name string, or the legacy singular {"tumor_slide": ...}."""
    if isinstance(payload, list) and len(payload) == 1 and isinstance(payload[0], dict):
        payload = payload[0]
    if isinstance(payload, dict):
        if "tumor_slides" in payload:
            payload = payload["tumor_slides"]
        elif "tumor_slide" in payload:
            payload = payload["tumor_slide"]
        else:
            return None, "submission has no `tumor_slides` field"
    if payload is None:
        return None, "`tumor_slides` is null"
    if isinstance(payload, str):
        payload = [payload]
    if not isinstance(payload, list):
        return None, "`tumor_slides` must be a list of slide names"
    names: set[str] = set()
    for item in payload:
        stem = _normalize_slide_name(item)
        if stem is None:
            return None, f"unrecognized slide entry: {item!r}"
        names.add(stem)
    return names, None


def main() -> int:
    args = _parse_args()
    for path in (args.reward_txt, args.metrics_json, args.error_analysis_file):
        path.parent.mkdir(parents=True, exist_ok=True)

    answer_key = json.loads(args.answer_key.read_text(encoding="utf-8"))
    expected = {_normalize_slide_name(s) for s in answer_key["tumor_slides"]}
    candidates = {_normalize_slide_name(s) for s in answer_key.get("slides", [])}

    error: str | None = None
    raw_payload: Any = None
    predicted: set[str] | None = None
    if not args.submission.exists():
        error = "missing submission"
    else:
        try:
            raw_payload = json.loads(args.submission.read_text(encoding="utf-8"))
            predicted, error = _extract_prediction(raw_payload)
        except json.JSONDecodeError as exc:
            error = f"submission is not valid JSON: {exc}"

    pred = predicted or set()
    unknown = sorted(pred - candidates) if candidates else []
    tp = len(pred & expected)
    fp = len(pred - expected)
    fn = len(expected - pred)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    correct = error is None and pred == expected
    reward = 1.0 if correct else 0.0

    metrics = {
        "reward": reward,
        "correct": correct,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "n_slides": len(candidates),
        "n_expected_tumor_slides": len(expected),
        "n_predicted_tumor_slides": len(pred),
        "error": error,
    }
    args.reward_txt.write_text(f"{reward:.6f}\n", encoding="utf-8")
    args.metrics_json.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    args.error_analysis_file.write_text(
        json.dumps(
            {
                "task_id": answer_key.get("task_id"),
                "raw_submission": raw_payload,
                "predicted_tumor_slides": sorted(pred),
                "expected_tumor_slides": sorted(expected),
                "unknown_slide_names": unknown,
                "candidates": sorted(candidates),
                "correct": correct,
                "error": error,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
