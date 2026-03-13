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
    answer_key_rows = _load_json(args.task_dir / "tests" / "task_answer_key.json")
    answers_by_id = {str(row.get("task_id", row.get("id", ""))): row for row in answer_key_rows}

    results: list[dict[str, Any]] = []
    for task in benchmark:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id", ""))
        answer_key = answers_by_id.get(task_id, {})
        row: dict[str, Any] = {
            "task_id": task_id,
            "instruction": task.get("instruction", ""),
            "final_answer": "",
            "payload": answer_key.get("payload"),
        }
        expected = answer_key.get("sol", "")
        if isinstance(expected, list) and len(expected) == 1:
            expected = expected[0]
        if task_id.startswith(("task3", "task8")):
            row["final_answer"] = ""
        else:
            row["final_answer"] = expected
        results.append(row)

    payload = json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        sys.stdout.write(payload)
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
