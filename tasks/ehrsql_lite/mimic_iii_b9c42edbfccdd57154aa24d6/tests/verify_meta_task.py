#!/usr/bin/env python3
"""Harbor verifier for EHRSQL meta-task.

This script is called by Harbor after the agent completes to evaluate the submission.
It reads submission.json, compares against answer_key.json, and outputs verification results.

Usage (called by Harbor automatically):
    python tasks/ehrsql_lite/tests/verify_meta_task.py

Expected environment:
    - /workspace/submission.json — agent's answers
    - /workspace/benchmark_tasks.json — task definitions
    - /tests/task_answer_key.json — expected answers
    - /tests/evaluator.py — evaluation logic (copied from scripts/ehrsql/)
    - /data/ehrsql/ — SQLite database files (mounted from scripts/ehrsql/assets)
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
    db_dir = Path("/data/ehrsql")  # Mount point for scripts/ehrsql/assets/ → /data/ehrsql/mimic_iii/mimic_iii.sqlite

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
        (logs_dir / "reward.json").write_text(json.dumps({
            "pred_not_null": 0, "real_not_null": 0, "both_not_null": 0,
            "exec_match_given_pred": 0, "exec_match_given_real": 0,
            "total": 0, "passed": 0,
        }))
        return 1

    if not answer_key_path.exists():
        result = {
            "status": "error",
            "error": f"Answer key not found: {answer_key_path}",
        }
        (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
        (logs_dir / "reward.json").write_text(json.dumps({
            "pred_not_null": 0, "real_not_null": 0, "both_not_null": 0,
            "exec_match_given_pred": 0, "exec_match_given_real": 0,
            "total": 0, "passed": 0,
        }))
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
        (logs_dir / "reward.json").write_text(json.dumps({
            "pred_not_null": 0, "real_not_null": 0, "both_not_null": 0,
            "exec_match_given_pred": 0, "exec_match_given_real": 0,
            "total": 0, "passed": 0,
        }))
        return 1

    # Count how many rows the agent actually filled before evaluation normalizes them
    filled = sum(1 for r in submission if r.get("final_answer", "").strip())

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
        (logs_dir / "reward.json").write_text(json.dumps({
            "pred_not_null": 0, "real_not_null": 0, "both_not_null": 0,
            "exec_match_given_pred": 0, "exec_match_given_real": 0,
            "total": 0, "passed": 0,
        }))
        return 1

    # Format results
    result = {
        "status": "success",
        "pass_at_1": eval_result["pass_at_1"],
        "total_tasks": eval_result["total_tasks"],
        "passed_tasks": eval_result["passed_tasks"],
        "failed_tasks": eval_result["failed_tasks"],
        "metrics": {
            "answerability": {
                "precision": eval_result["precision_ans"],
                "recall": eval_result["recall_ans"],
                "f1": eval_result["f1_ans"],
            },
            "execution": {
                "precision": eval_result["precision_exec"],
                "recall": eval_result["recall_exec"],
                "f1": eval_result["f1_exec"],
            },
        },
        "summary": {
            "total": eval_result["total_tasks"],
            "passed": eval_result["passed_tasks"],
            "accuracy": f"{eval_result['pass_at_1']:.2%}",
        },
    }

    # Write outputs
    (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))

    # Write structured rewards for Harbor metric aggregation.
    # NOTE: Do NOT write reward.txt — Harbor prefers it over reward.json,
    # and the aggregate metric needs the structured counts from reward.json.
    # Emit raw binary indicators per question so the aggregate metric can
    # sum across all tasks and compute global precision/recall/F1 exactly
    # as harbor_evaluator.py does.
    reward_json: dict[str, int] = {
        "pred_not_null": 0,
        "real_not_null": 0,
        "both_not_null": 0,
        "exec_match_given_pred": 0,
        "exec_match_given_real": 0,
        "total": 0,
        "passed": 0,
        "filled": filled,
    }
    for r in eval_result["results"]:
        pred = r["predicted_result"]
        real = r["expected_result"]
        pred_ans = pred != "null"
        real_ans = real != "null"
        match = real == pred

        reward_json["total"] += 1
        if r["success"]:
            reward_json["passed"] += 1
        if pred_ans:
            reward_json["pred_not_null"] += 1
        if real_ans:
            reward_json["real_not_null"] += 1
        if pred_ans and real_ans:
            reward_json["both_not_null"] += 1
        if pred_ans and match:
            reward_json["exec_match_given_pred"] += 1
        if real_ans and match:
            reward_json["exec_match_given_real"] += 1

    (logs_dir / "reward.json").write_text(json.dumps(reward_json))

    # Save detailed results for debugging (SQL queries and outputs for each task)
    detailed_results = {
        "summary": {
            "total_tasks": eval_result["total_tasks"],
            "passed_tasks": eval_result["passed_tasks"],
            "failed_tasks": eval_result["failed_tasks"],
            "pass_at_1": eval_result["pass_at_1"],
        },
        "tasks": eval_result["results"],
    }
    (logs_dir / "detailed_results.json").write_text(json.dumps(detailed_results, indent=2))

    # Print to stdout
    print(json.dumps(result, indent=2))

    # Return success if any tasks passed, or partial success if we evaluated
    return 0 if eval_result["passed_tasks"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
