#!/usr/bin/env python3
"""Per-task verifier entry point. Calls harbor_evaluator.evaluate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harbor_evaluator import evaluate  # noqa: E402


def main() -> None:
    submission = Path("/workspace/submission/predictions.txt")
    gold = Path(__file__).resolve().parent / "gold.json"
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, gold, log_dir)
    print(f"reward={score:.6f}")


if __name__ == "__main__":
    main()
