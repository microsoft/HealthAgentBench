#!/usr/bin/env python3
"""Per-task verifier entry point. Calls harbor_evaluator.evaluate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harbor_evaluator import evaluate  # noqa: E402


def main() -> None:
    submission = Path("/workspace/submission/run.txt")
    qrels = Path(__file__).resolve().parent / "qrels.txt"
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, qrels, log_dir)
    print(f"ndcg_cut_10={score:.6f}")


if __name__ == "__main__":
    main()
