#!/usr/bin/env python3
"""Convert MedAgentBench task JSON into canonical YAML manifests."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

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

ACTION_MED_TASK_TYPES = {
    "recording_patient_data",
    "test_ordering",
    "medication_ordering",
}


def _load_tasks(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        tasks = raw
    elif isinstance(raw, dict) and isinstance(raw.get("tasks"), list):
        tasks = raw["tasks"]
    else:
        raise ValueError("Input JSON must be a list or object with a 'tasks' list.")
    return [dict(task) for task in tasks]


def _infer_group(task_id: str) -> str:
    match = re.match(r"^(task\d+)_", task_id)
    return match.group(1) if match else "unknown"


def _parse_tool_names(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []

    tool_names: list[str] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        if "Condition" in name and "GET" in name:
            tool_names.append("condition_search")
        elif "Observation" in name and "Labs" in str(item.get("description", "")):
            tool_names.append("lab_search")
        elif (
            "Observation" in name
            and "Vitals" in str(item.get("description", ""))
            and "GET" in name
        ):
            tool_names.append("vital_search")
        elif "Observation" in name and "POST" in name:
            tool_names.append("vital_create")
        elif "MedicationRequest" in name and "GET" in name:
            tool_names.append("medicationrequest_search")
        elif "MedicationRequest" in name and "POST" in name:
            tool_names.append("medicationrequest_create")
        elif "Procedure" in name and "GET" in name:
            tool_names.append("procedure_search")
        elif "ServiceRequest" in name and "POST" in name:
            tool_names.append("procedure_create")
        elif "Patient" in name and "GET" in name:
            tool_names.append("patient_search")

    return sorted(set(tool_names))


def _normalize(
    task: dict[str, Any], *, split: str, allowed_tools: list[str]
) -> dict[str, Any]:
    task_id = str(task.get("id", task.get("task_id", "")))
    group = _infer_group(task_id)
    med_task_type = GROUP_TO_MED_TASK_TYPE.get(group, "patient_information_retrieval")
    repo_task_type = MED_TASK_TYPE_TO_REPO_TASK_TYPE[med_task_type]
    query_or_action = "action" if med_task_type in ACTION_MED_TASK_TYPES else "query"

    instruction = str(task.get("instruction", ""))
    context = str(task.get("context", "")).strip()
    if context:
        instruction = f"{instruction}\n\nContext: {context}"

    expected_answer: Any = task.get("sol", "")
    if isinstance(expected_answer, list) and len(expected_answer) == 1:
        expected_answer = expected_answer[0]

    return {
        "task_id": task_id,
        "category": repo_task_type,
        "difficulty": "medium" if query_or_action == "action" else "easy",
        "instruction": instruction,
        "expected_answer": expected_answer,
        "required_actions": [] if query_or_action == "query" else [med_task_type],
        "split": split,
        "task_type": query_or_action,
        "backend_profile": "fhir",
        "source_benchmark": "medagentbench",
        "source_group": group,
        "source_task_type": med_task_type,
        "eval_mrn": task.get("eval_MRN"),
        "allowed_tools": allowed_tools,
    }


def _task_type_slug(value: str) -> str:
    lowered = value.strip().lower().replace("-", " ").replace("/", " ")
    return re.sub(r"[^a-z0-9]+", "_", lowered).strip("_") or "unknown"


def _write_manifest(path: Path, tasks: list[dict[str, Any]]) -> None:
    payload = {"tasks": tasks}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--output-root")
    parser.add_argument("--funcs-json")
    parser.add_argument("--split", default="std")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    output_root = Path(args.output_root) if args.output_root else None
    funcs_path = Path(args.funcs_json) if args.funcs_json else None

    if not output_path and not output_root:
        raise SystemExit(
            "Provide --output for a single file or --output-root for grouped manifests."
        )

    allowed_tools = _parse_tool_names(funcs_path)
    tasks = [
        _normalize(t, split=args.split, allowed_tools=allowed_tools)
        for t in _load_tasks(input_path)
    ]
    tasks.sort(key=lambda item: item["task_id"])

    if output_path:
        _write_manifest(output_path, tasks)
        print(f"wrote {len(tasks)} tasks to {output_path}")

    if output_root:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for task in tasks:
            task_type = _task_type_slug(str(task["category"]))
            split = str(task.get("split", "std"))
            key = (task_type, split)
            grouped.setdefault(key, []).append(task)

        for (task_type, split), task_rows in sorted(grouped.items()):
            manifest_path = (
                output_root / task_type / "sources" / "medagentbench" / f"{split}.yaml"
            )
            _write_manifest(manifest_path, task_rows)
            print(f"wrote {len(task_rows)} tasks to {manifest_path}")


if __name__ == "__main__":
    main()
