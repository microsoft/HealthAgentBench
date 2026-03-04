#!/usr/bin/env python3
"""Convert MedAgentBench task JSON into canonical YAML manifests."""

from __future__ import annotations

import argparse
import json
import re
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


def _task_type_slug(value: str) -> str:
    lowered = value.strip().lower().replace("-", " ").replace("/", " ")
    return re.sub(r"[^a-z0-9]+", "_", lowered).strip("_") or "unknown"


def _write_manifest(path: Path, tasks: list[dict[str, Any]]) -> None:
    payload = {"tasks": tasks}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--output-root")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    output_root = Path(args.output_root) if args.output_root else None

    if not output_path and not output_root:
        raise SystemExit("Provide --output for a single file or --output-root for grouped manifests.")

    tasks = [_normalize(t) for t in _load_tasks(input_path)]
    tasks.sort(key=lambda item: item["task_id"])

    if output_path:
        _write_manifest(output_path, tasks)
        print(f"wrote {len(tasks)} tasks to {output_path}")

    if output_root:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for task in tasks:
            task_type = _task_type_slug(str(task.get("category", "unknown")))
            split = str(task.get("split", "std"))
            key = (task_type, split)
            grouped.setdefault(key, []).append(task)

        for (task_type, split), task_rows in sorted(grouped.items()):
            manifest_path = output_root / task_type / "sources" / "medagentbench" / f"{split}.yaml"
            _write_manifest(manifest_path, task_rows)
            print(f"wrote {len(task_rows)} tasks to {manifest_path}")


if __name__ == "__main__":
    main()
