#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluator import evaluate_results


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_tool_trace(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        if "args" in entry and isinstance(entry.get("args"), dict):
            normalized.append(entry)
            continue
        tool = entry.get("tool")
        resource = entry.get("resource")
        if isinstance(tool, str) and isinstance(resource, dict):
            normalized.append(
                {
                    "tool": tool,
                    "status": entry.get("status", "ok"),
                    "args": {"resource": resource},
                }
            )
    return normalized


def _build_results(tasks_payload: dict[str, Any], submission_payload: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = tasks_payload.get("tasks", [])
    submitted_rows = submission_payload.get("results", [])
    submitted_by_id = {
        str(row.get("task_id")): row
        for row in submitted_rows
        if isinstance(row, dict) and row.get("task_id")
    }

    rows: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id", ""))
        submitted = submitted_by_id.get(task_id, {})
        row = dict(task)
        row["final_answer"] = submitted.get("final_answer", "")
        row["tool_trace"] = _normalize_tool_trace(submitted.get("tool_trace", []))
        if task_id not in submitted_by_id:
            row["error_type"] = "missing_submission"
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--reward-file", type=Path, required=True)
    args = parser.parse_args()

    if not args.submission.exists():
        args.reward_file.write_text("0\n", encoding="utf-8")
        print(f"missing submission file: {args.submission}")
        return

    tasks_payload = _load_json(args.tasks)
    submission_payload = _load_json(args.submission)
    rows = _build_results(tasks_payload, submission_payload)

    results_path = args.reward_file.parent / "meta_results.jsonl"
    with results_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = evaluate_results(str(results_path))
    args.reward_file.write_text(f"{summary['pass_at_1']:.6f}\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
