#!/usr/bin/env python3
"""Convert MedAgentBench task JSON into canonical YAML manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_tasks(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        tasks = raw
    elif isinstance(raw, dict) and isinstance(raw.get("tasks"), list):
        tasks = raw["tasks"]
    else:
        raise ValueError("Input JSON must be a list or object with a 'tasks' list.")
    return [dict(task) for task in tasks]


def _normalize(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": str(task.get("task_id", "")),
        "category": str(task.get("category", "unknown")),
        "difficulty": str(task.get("difficulty", "unknown")),
        "instruction": str(task.get("instruction", "")),
        "expected_answer": task.get("expected_answer", ""),
        "required_actions": list(task.get("required_actions", [])),
        "split": str(task.get("split", "std")),
        "task_type": str(task.get("task_type", "query")),
        "backend_profile": str(task.get("backend_profile", "fhir")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    tasks = [_normalize(t) for t in _load_tasks(input_path)]
    tasks.sort(key=lambda item: item["task_id"])

    payload = {"tasks": tasks}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )

    print(f"wrote {len(tasks)} tasks to {output_path}")


if __name__ == "__main__":
    main()
