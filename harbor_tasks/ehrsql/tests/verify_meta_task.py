#!/usr/bin/env python3
"""Harbor verifier for EHRSQL meta-task.

This script is called by Harbor after the agent completes to evaluate the submission.
It reads submission.json, compares against answer_key.json, and outputs verification results.

Usage (called by Harbor automatically):
    python harbor_tasks/ehrsql/tests/verify_meta_task.py

Expected environment:
    - /workspace/submission.json — agent's answers
    - /workspace/benchmark_tasks.json — task definitions
    - /tests/task_answer_key.json — expected answers
    - /tests/evaluator.py — evaluation logic (copied from scripts/ehrsql/)
    - /data/ehrsql/ — SQLite database files
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Import evaluator from local tests directory (self-contained)
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from evaluator import evaluate_submission_rows


def main() -> int:
    """Main verifier entry point."""
    # Harbor paths
    workspace_dir = Path("/workspace")
    tests_dir = Path("/tests")
    logs_dir = Path("/logs/verifier")
    db_dir = Path("/data/ehrsql")

    # Create logs directory
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Load submission and answer key
    submission_path = workspace_dir / "submission.json"
    answer_key_path = tests_dir / "task_answer_key.json"

    if not submission_path.exists():
        result = {
            "status": "error",
            "error": f"Submission not found: {submission_path}",
        }
        (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
        (logs_dir / "reward.txt").write_text("0.0")
        return 1

    if not answer_key_path.exists():
        result = {
            "status": "error",
            "error": f"Answer key not found: {answer_key_path}",
        }
        (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
        (logs_dir / "reward.txt").write_text("0.0")
        return 1

    try:
        submission = json.loads(submission_path.read_text())
        answer_key = json.loads(answer_key_path.read_text())
    except json.JSONDecodeError as e:
        result = {
            "status": "error",
            "error": f"Failed to parse JSON: {str(e)}",
        }
        (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
        (logs_dir / "reward.txt").write_text("0.0")
        return 1

    # Save agent's submission for inspection/debugging
    (logs_dir / "submission.json").write_text(json.dumps(submission, indent=2))

    # Evaluate submission
    try:
        eval_result = evaluate_submission_rows(submission, answer_key, db_dir)
    except Exception as e:
        result = {
            "status": "error",
            "error": f"Evaluation failed: {str(e)}",
        }
        (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
        (logs_dir / "reward.txt").write_text("0.0")
        return 1

    # Format results
    result = {
        "status": "success",
        "pass_at_1": eval_result["pass_at_1"],
        "total_tasks": eval_result["total_tasks"],
        "passed_tasks": eval_result["passed_tasks"],
        "failed_tasks": eval_result["failed_tasks"],
        "error_taxonomy": eval_result["error_taxonomy"],
        "summary": {
            "total": eval_result["total_tasks"],
            "passed": eval_result["passed_tasks"],
            "accuracy": f"{eval_result['pass_at_1']:.2%}",
        },
    }

    # Write outputs
    (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
    (logs_dir / "reward.txt").write_text(f"{eval_result['pass_at_1']:.4f}")

    # Print to stdout
    print(json.dumps(result, indent=2))

    # Return success if any tasks passed, or partial success if we evaluated
    return 0 if eval_result["passed_tasks"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
