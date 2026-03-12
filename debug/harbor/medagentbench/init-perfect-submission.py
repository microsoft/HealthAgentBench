#!/usr/bin/env python3
"""Build a perfect synthetic submission for the generated MedAgentBench Harbor task.

Args:
    --task-dir: Generated Harbor task directory used as the source of benchmark metadata.
    --output: Path to write the generated submission JSON. Defaults to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    """Load a UTF-8 JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task-dir",
        type=Path,
        default=Path("harbor_tasks/medagentbench"),
        help="Generated Harbor task directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path for the generated submission JSON.",
    )
    args = parser.parse_args()

    workspace_dir = args.task_dir / "environment" / "workspace"
    benchmark = _load_json(workspace_dir / "benchmark_tasks.json")
    action_templates = _load_json(workspace_dir / "action_payload_templates.json")

    results: list[dict[str, Any]] = []
    for task in benchmark.get("tasks", []):
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id", ""))
        row: dict[str, Any] = {"task_id": task_id, "final_answer": "", "tool_trace": []}
        if task.get("evaluation_focus") == "tool_trace":
            row["tool_trace"] = action_templates.get(task_id, {}).get("tool_trace", [])
        else:
            row["final_answer"] = task.get("expected_answer", "")
        results.append(row)

    payload = json.dumps({"results": results}, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        sys.stdout.write(payload)
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
