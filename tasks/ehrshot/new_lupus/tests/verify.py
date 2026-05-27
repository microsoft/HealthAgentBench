#!/usr/bin/env python3
"""Per-task verifier entry point. Calls harbor_evaluator.evaluate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harbor_evaluator import evaluate  # noqa: E402


def main() -> None:
    here = Path(__file__).resolve().parent
    submission = Path("/workspace/submission/predictions.csv")
    test_labels = here / "test_labels.csv"   # written by bootstrap at run time
    baseline = here / "baseline.json"
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, test_labels, baseline, log_dir)
    print(f"auroc={score:.6f}")


if __name__ == "__main__":
    main()
