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


def default_selected_task_ids(raw_tasks: list[dict[str, Any]], sample_size: int = 200) -> list[str]:
    """Select a deterministic random sample of tasks for the benchmark.

    Strategy: Randomly sample tasks with a fixed seed for reproducibility.
    - Default: 200 tasks (or all if fewer available)
    - Customizable via sample_size parameter
    - DETERMINISTIC: Same sample_size always produces same tasks (seed=42)

    Args:
        raw_tasks: List of all raw EHRSQL tasks
        sample_size: Target number of tasks to select (default 200)

    Returns:
        List of randomly selected task IDs
    """
    import random
    rng = random.Random(42)  # Fixed seed for determinism
    all_ids = [str(t.get("id")) for t in raw_tasks if t.get("id")]
    if len(all_ids) <= sample_size:
        # If we have fewer tasks than sample_size, return all
        return all_ids
    # Random sample without replacement (deterministic with seed=42)
    return rng.sample(all_ids, sample_size)


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
