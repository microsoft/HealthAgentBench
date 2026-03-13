"""Shared normalization helpers for MedAgentBench raw-task ingestion."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


GROUP_TO_MED_TASK_TYPE: dict[str, str] = {
    "task1": "patient_information_retrieval",
    "task2": "patient_information_retrieval",
    "task3": "recording_patient_data",
    "task4": "lab_result_retrieval",
    "task5": "medication_ordering",
    "task6": "patient_data_aggregation",
    "task7": "lab_result_retrieval",
    "task8": "test_ordering",
    "task9": "medication_ordering",
    "task10": "test_ordering",
}

MED_TASK_TYPE_TO_REPO_TASK_TYPE: dict[str, str] = {
    "patient_information_retrieval": "factual_qa",
    "lab_result_retrieval": "factual_qa",
    "patient_data_aggregation": "data_aggregation",
    "recording_patient_data": "clinical_data_recording",
    "test_ordering": "care_ordering",
    "medication_ordering": "medication_reconciliation",
}

ACTION_GROUPS = {"task3", "task5", "task8", "task9", "task10"}


def load_raw_tasks(path: Path) -> list[dict[str, Any]]:
    """Load the original MedAgentBench task JSON."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        tasks = raw
    elif isinstance(raw, dict) and isinstance(raw.get("tasks"), list):
        tasks = raw["tasks"]
    else:
        raise ValueError("Input JSON must be a list or object with a 'tasks' list.")
    return [dict(task) for task in tasks]


def infer_group(task_id: str) -> str:
    """Infer the `taskN` group from a MedAgentBench task id."""
    match = re.match(r"^(task\d+)_", task_id)
    return match.group(1) if match else "unknown"


def group_sort_key(value: str) -> tuple[int, str]:
    """Sort `taskN` groups numerically when possible."""
    suffix = value.removeprefix("task")
    return (int(suffix) if suffix.isdigit() else 10**9, value)


def default_selected_task_ids(raw_tasks: list[dict[str, Any]]) -> list[str]:
    """Select the default one-per-group MedAgentBench slice."""
    grouped: dict[str, set[str]] = {}
    for row in raw_tasks:
        task_id = str(row.get("id", row.get("task_id", ""))).strip()
        group = infer_group(task_id)
        if group == "unknown" or not task_id:
            continue
        grouped.setdefault(group, set()).add(task_id)

    selected: list[str] = []
    for group in sorted(grouped, key=group_sort_key):
        preferred = f"{group}_1"
        if preferred not in grouped[group]:
            raise ValueError(
                f"Expected representative task {preferred} for group {group}, "
                f"but available task IDs are {sorted(grouped[group])[:5]}..."
            )
        selected.append(preferred)
    return selected


def build_instruction(
    *,
    base_instruction: str,
    context: str,
    source_group: str,
) -> str:
    """Merge raw instruction/context and apply MedAgentBench answer formatting hints."""
    parts: list[str] = [base_instruction.strip()]
    if context.strip():
        parts.append(f"Context: {context.strip()}")

    if source_group == "task1":
        mentions_not_found = "patient not found" in (base_instruction + context).lower()
        if mentions_not_found:
            parts.append(
                "Final answer format requirement: return only the MRN string "
                '(for example "S1234567"), or "Patient not found". '
                "Do not include any extra text."
            )
        else:
            parts.append(
                "Final answer format requirement: return only the MRN string "
                '(for example "S1234567"). Do not include any extra text.'
            )
    elif source_group in {"task2", "task4", "task6", "task7"}:
        parts.append(
            "Final answer format requirement: return only a single numeric value. "
            "Do not include any extra text."
        )
    elif source_group == "task10":
        parts.append(
            "Final answer format requirement: return [-1] if no qualifying measurement is available; "
            "otherwise return [value, timestamp]."
        )
    elif source_group in {"task5", "task9"}:
        parts.append(
            "Final answer format requirement: return only a single numeric value "
            "(or -1 if no measurement is available). Do not include any extra text."
        )

    return "\n\n".join(part for part in parts if part)


def normalize_harbor_task(row: dict[str, Any]) -> dict[str, Any]:
    """Build the minimal normalized task payload used by Harbor benchmark metadata."""
    task_id = str(row.get("id", row.get("task_id", "")))
    group = infer_group(task_id)
    med_task_type = GROUP_TO_MED_TASK_TYPE.get(group, "patient_information_retrieval")
    category = MED_TASK_TYPE_TO_REPO_TASK_TYPE[med_task_type]
    difficulty = "medium" if group in ACTION_GROUPS else "easy"
    expected_answer: Any = row.get("sol", "")
    if isinstance(expected_answer, list) and len(expected_answer) == 1:
        expected_answer = expected_answer[0]
    if group == "task10" and expected_answer == -1:
        expected_answer = [-1]
    return {
        "task_id": task_id,
        "category": category,
        "difficulty": difficulty,
        "instruction": build_instruction(
            base_instruction=str(row.get("instruction", "")),
            context=str(row.get("context", "")),
            source_group=group,
        ),
        "expected_answer": expected_answer,
        "source_benchmark": "medagentbench",
        "eval_mrn": row.get("eval_MRN"),
    }
