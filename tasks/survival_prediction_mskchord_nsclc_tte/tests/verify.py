#!/usr/bin/env python3
"""Per-task verifier entry point."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harbor_evaluator import evaluate


def main() -> None:
    here = Path(__file__).resolve().parent
    reward = evaluate(
        submission_path=Path("/workspace/submission/predictions.csv"),
        test_labels_path=here / "test_labels.csv",
        train_outcomes_path=here / "train_outcomes.csv",
        baseline_path=here / "baseline.json",
        log_dir=Path("/logs/verifier"),
        artifact_dir=Path("/logs/artifacts"),
    )
    print(f"reward={reward:.6f}")


if __name__ == "__main__":
    main()
