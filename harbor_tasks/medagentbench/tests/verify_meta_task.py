#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluator import evaluate_submission_rows


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_submission(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    raise ValueError("submission.json must be a list or an object with a 'results' list")


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

    task_payload = _load_json(args.tasks)
    expected_ids = [row["task_id"] for row in task_payload.get("tasks", []) if isinstance(row, dict)]
    submission_rows = _normalize_submission(_load_json(args.submission))
    submitted_by_id = {
        str(row.get("id", row.get("task_id", ""))): row
        for row in submission_rows
        if isinstance(row, dict)
    }

    rows = []
    for task_id in expected_ids:
        row = submitted_by_id.get(task_id)
        if row is None:
            row = {"id": task_id, "final_answer": "", "payload": None}
        rows.append(row)

    summary = evaluate_submission_rows(rows)
    results_path = args.reward_file.parent / "meta_results.json"
    results_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.reward_file.write_text(f"{summary['pass_at_1']:.6f}\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
