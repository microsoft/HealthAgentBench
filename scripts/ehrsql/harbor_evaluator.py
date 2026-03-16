"""EHRSQL Harbor evaluator for SQL execution-based answer verification."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


def execute_sql(
    query: str,
    db_id: str,
    db_dir: Path,
    timeout: int = 30,
) -> dict[str, Any]:
    """Execute a SQL query against a database.

    Args:
        query: SQL query string
        db_id: Database ID (mimic_iii or eicu)
        db_dir: Base directory containing SQLite files
        timeout: Query timeout in seconds

    Returns:
        Result dict with status, row_count, columns, rows, or error
    """
    if query == "null" or query is None:
        return {"status": "null", "row_count": 0, "columns": [], "rows": []}

    db_file = db_dir / db_id / f"{db_id}.sqlite"

    if not db_file.exists():
        return {
            "status": "error",
            "error": f"Database file not found: {db_file}",
        }

    try:
        conn = sqlite3.connect(str(db_file))
        conn.timeout = timeout
        cursor = conn.cursor()

        cursor.execute(query)
        rows = cursor.fetchall()

        col_names = [desc[0] for desc in cursor.description] if cursor.description else []

        results = {
            "status": "success",
            "row_count": len(rows),
            "columns": col_names,
            "rows": [dict(zip(col_names, row)) for row in rows],
        }

        conn.close()
        return results
    except sqlite3.Error as e:
        return {
            "status": "error",
            "error": str(e),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
        }


def _normalize_result_set(result: dict[str, Any]) -> set[tuple[Any, ...]] | None:
    """Convert SQL result to a normalized set of tuples for comparison.

    Handles different data types and orderings.

    Args:
        result: Execution result dict

    Returns:
        Set of tuples (one per row), None if error or null
    """
    if result.get("status") == "null":
        return None
    if result.get("status") != "success":
        return None

    rows = result.get("rows", [])
    columns = result.get("columns", [])

    if not columns:
        return set()

    # Convert each row to tuple, handling None values and type normalization
    tuples = set()
    for row in rows:
        values = tuple(row.get(col) for col in columns)
        tuples.add(values)

    return tuples


def _compare_result_sets(
    gold_result: dict[str, Any],
    pred_result: dict[str, Any],
) -> tuple[bool, str]:
    """Compare two SQL result sets for equivalence.

    Args:
        gold_result: Gold SQL execution result
        pred_result: Predicted SQL execution result

    Returns:
        (success: bool, reason: str)
    """
    # Both null -> answerability check will handle
    if gold_result.get("status") == "null" and pred_result.get("status") == "null":
        return True, "both_null"

    # Only one is null -> failure (unanswerable detection failure)
    if gold_result.get("status") == "null" or pred_result.get("status") == "null":
        return False, "answerability_mismatch"

    # Gold error -> can't evaluate
    if gold_result.get("status") == "error":
        return False, "gold_error"

    # Predicted error -> failure
    if pred_result.get("status") == "error":
        return False, "execution_error"

    # Normalize both result sets
    gold_set = _normalize_result_set(gold_result)
    pred_set = _normalize_result_set(pred_result)

    if gold_set is None or pred_set is None:
        return False, "normalization_error"

    # Compare sets
    if gold_set == pred_set:
        return True, "match"
    else:
        return False, "result_mismatch"


def evaluate_submission_rows(
    submission_rows: list[dict[str, Any]],
    answer_key_rows: list[dict[str, Any]],
    db_dir: Path,
) -> dict[str, Any]:
    """Evaluate submitted answers against answer key.

    Args:
        submission_rows: Agent-submitted answers from submission.json
        answer_key_rows: Expected answers from answer key
        db_dir: Base directory containing SQLite files

    Returns:
        Evaluation summary with pass_at_1, per-task results, error taxonomy
    """
    # Index answer key by task_id
    answer_key = {row["task_id"]: row for row in answer_key_rows}

    results = []
    passed = 0
    error_counts = {}

    for sub in submission_rows:
        task_id = sub.get("task_id")
        pred_sql = sub.get("final_answer", "")
        expected_sql = answer_key.get(task_id, {}).get("expected_answer", "")
        db_id = answer_key.get(task_id, {}).get("db_id", "mimic_iii")

        # Execute both queries
        gold_result = execute_sql(expected_sql, db_id, db_dir)
        pred_result = execute_sql(pred_sql, db_id, db_dir)

        # Compare results
        success, reason = _compare_result_sets(gold_result, pred_result)

        if success:
            passed += 1

        error_counts[reason] = error_counts.get(reason, 0) + 1

        results.append(
            {
                "task_id": task_id,
                "submitted_sql": pred_sql,
                "expected_sql": expected_sql,
                "success": success,
                "reason": reason,
                "gold_result": gold_result,
                "pred_result": pred_result,
            }
        )

    total = len(submission_rows)
    pass_at_1 = passed / total if total > 0 else 0.0

    return {
        "pass_at_1": pass_at_1,
        "total_tasks": total,
        "passed_tasks": passed,
        "failed_tasks": total - passed,
        "error_taxonomy": error_counts,
        "results": results,
    }


def merge_submission_with_answer_key(
    submission_rows: list[dict[str, Any]],
    answer_key_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Merge submitted answers with answer keys by task_id.

    Args:
        submission_rows: Agent submission
        answer_key_rows: Expected answers

    Returns:
        (merged_rows, mismatched_task_ids)
    """
    answer_key = {row["task_id"]: row for row in answer_key_rows}
    submission = {row["task_id"]: row for row in submission_rows}

    merged = []
    mismatched = []

    for task_id in answer_key.keys():
        sub = submission.get(task_id)
        key = answer_key[task_id]

        if not sub:
            mismatched.append(task_id)
            continue

        merged.append({**key, **{"submitted": sub}})

    return merged, mismatched


if __name__ == "__main__":
    # Example standalone usage
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--submission", required=True)
    parser.add_argument("--answer-key", required=True)
    parser.add_argument("--db-dir", default="/data/ehrsql")
    args = parser.parse_args()

    submission = json.loads(Path(args.submission).read_text())
    answer_key = json.loads(Path(args.answer_key).read_text())

    result = evaluate_submission_rows(submission, answer_key, Path(args.db_dir))
    print(json.dumps(result, indent=2))
