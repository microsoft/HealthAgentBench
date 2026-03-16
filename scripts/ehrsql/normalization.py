"""EHRSQL task normalization helpers for Harbor task generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# EHRSQL is fundamentally text-to-SQL Q&A over EHR databases
# Maps to factual_qa in the repo task type system
EHRSQL_TASK_TYPE_TO_REPO_TASK_TYPE = {
    "text_to_sql": "factual_qa",
}

# EHRSQL difficulty mapping from `importance` field
IMPORTANCE_TO_DIFFICULTY = {
    "high": "hard",
    "medium": "medium",
    "low": "easy",
    "n/a": "easy",
}


def load_raw_tasks(path: Path) -> list[dict[str, Any]]:
    """Load EHRSQL task JSON from a file.

    Args:
        path: Path to the JSON file (valid.json or test.json)

    Returns:
        List of task dictionaries
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [dict(task) for task in raw]
    elif isinstance(raw, dict) and isinstance(raw.get("tasks"), list):
        return [dict(task) for task in raw["tasks"]]
    else:
        raise ValueError("Input JSON must be a list or object with a 'tasks' list.")


def infer_db_id(task: dict[str, Any]) -> str:
    """Extract database ID from task.

    Args:
        task: Task dictionary

    Returns:
        db_id (e.g., "mimic_iii" or "eicu")
    """
    return str(task.get("db_id", "unknown"))


def infer_split(task: dict[str, Any]) -> str:
    """Extract dataset split from task.

    Args:
        task: Task dictionary

    Returns:
        split name (e.g., "valid" or "test")
    """
    return str(task.get("split", "valid"))


def build_instruction(
    *,
    base_question: str,
    db_id: str,
) -> str:
    """Build the Harbor instruction for an EHRSQL task.

    Args:
        base_question: The natural language question
        db_id: Database ID (mimic_iii or eicu)

    Returns:
        Formatted instruction with context and answer requirements
    """
    parts = [base_question.strip()]

    # Add database context
    db_name = "MIMIC-III" if db_id == "mimic_iii" else "eICU"
    parts.append(f"Database: {db_name}")

    # Add answer format requirements
    parts.append(
        "Your task: Generate a SQL query that answers the question. "
        "If the question cannot be answered with the available data, return 'null'. "
        "Consider using schema inspection tools to understand available tables and columns."
    )

    return "\n\n".join(parts)


def normalize_harbor_task(
    task: dict[str, Any], *, split: str
) -> dict[str, Any]:
    """Convert raw EHRSQL task to Harbor public payload.

    This is the agent-visible row with only task_id and instruction.

    Args:
        task: Raw EHRSQL task dictionary
        split: Dataset split (valid or test)

    Returns:
        Harbor task dict for public submission
    """
    db_id = infer_db_id(task)
    question = str(task.get("question", ""))

    # Generate task_id combining db and index
    task_id = task.get("id")
    if not task_id:
        # Fallback if no ID provided
        task_id = f"ehrsql_{db_id}_{split}_{hash(question) % 10000:04d}"
    else:
        task_id = f"ehrsql_{db_id}_{split}_{task_id}"

    return {
        "task_id": task_id,
        "instruction": build_instruction(
            base_question=question,
            db_id=db_id,
        ),
        "final_answer": "",
        "payload": None,  # No payload for text-to-SQL (read-only)
    }


def build_harbor_answer_key(
    task: dict[str, Any], *, split: str
) -> dict[str, Any]:
    """Build the Harbor answer key row (verifier-only) for an EHRSQL task.

    Args:
        task: Raw EHRSQL task dictionary
        split: Dataset split (valid or test)

    Returns:
        Harbor answer key row with expected_answer and metadata
    """
    db_id = infer_db_id(task)
    question = str(task.get("question", ""))
    is_impossible = task.get("is_impossible", False)

    # Task ID (must match normalize_harbor_task)
    task_id = task.get("id")
    if not task_id:
        task_id = f"ehrsql_{db_id}_{split}_{hash(question) % 10000:04d}"
    else:
        task_id = f"ehrsql_{db_id}_{split}_{task_id}"

    # Determine difficulty
    importance = str(task.get("importance", "n/a")).lower()
    difficulty = IMPORTANCE_TO_DIFFICULTY.get(importance, "easy")

    # Gold SQL query (for evaluation)
    gold_sql = task.get("query")
    if is_impossible or gold_sql == "nan" or gold_sql is None:
        gold_sql = "null"  # Unanswerable task
    else:
        gold_sql = str(gold_sql)

    return {
        "task_id": task_id,
        "category": "factual_qa",
        "difficulty": difficulty,
        "expected_answer": gold_sql,  # The gold SQL for comparison
        "db_id": db_id,
        "is_impossible": is_impossible,
        "importance": importance,
        "payload": None,
    }


def default_selected_task_ids(raw_tasks: list[dict[str, Any]]) -> list[str]:
    """Select a default slice of tasks for the benchmark.

    Strategy: Select 50 representative tasks (~25 per database, stratified by importance).
    This is a practical size for a single Harbor trial (completes in <5 min).

    Args:
        raw_tasks: List of all raw EHRSQL tasks

    Returns:
        List of selected task IDs
    """
    selected_by_db: dict[str, list[str]] = {"mimic_iii": [], "eicu": []}

    # Stratify by database and importance to get balanced coverage
    by_db_importance: dict[tuple[str, str], list[str]] = {}

    for task in raw_tasks:
        db_id = infer_db_id(task)
        importance = str(task.get("importance", "n/a")).lower()
        key = (db_id, importance)

        task_id = task.get("id")
        if task_id:
            if key not in by_db_importance:
                by_db_importance[key] = []
            by_db_importance[key].append(str(task_id))

    # Select ~3-4 tasks per (db, importance) combination to get ~25 per db
    for (db_id, importance), task_ids in sorted(by_db_importance.items()):
        # Take first 4 tasks from each importance level for each db
        selected_by_db[db_id].extend(task_ids[:4])

    # Return combined list, capped at 50 total
    result = selected_by_db["mimic_iii"] + selected_by_db["eicu"]
    return sorted(set(result))[:50]


def select_tasks(
    raw_tasks: list[dict[str, Any]], selected_task_ids: list[str]
) -> list[dict[str, Any]]:
    """Filter raw tasks by ID.

    Args:
        raw_tasks: List of all raw tasks
        selected_task_ids: List of task IDs to include

    Returns:
        Filtered list of tasks
    """
    selected_set = set(selected_task_ids)
    return [t for t in raw_tasks if str(t.get("id")) in selected_set]
