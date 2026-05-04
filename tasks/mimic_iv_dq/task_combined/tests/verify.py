#!/usr/bin/env python3
"""Per-task verifier entry point. Calls harbor_evaluator.evaluate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harbor_evaluator import evaluate  # noqa: E402


def main() -> None:
    submission = Path("/workspace/submission/flagged_rows.csv")
    # /tests/ is mounted by Harbor only at verifier-runtime; the agent phase
    # never sees this path. test.sh cd's here before invoking verify.py so
    # labels.csv resolves to the source-tree's tasks/<task>/tests/labels.csv.
    labels = Path(__file__).resolve().parent / "labels.csv"
    log_dir = Path("/logs/verifier")
    f1 = evaluate(submission, labels, log_dir)
    print(f"f1={f1:.6f}")


if __name__ == "__main__":
    main()
