#!/usr/bin/env python3
"""Update final_answer for a row in submission.json."""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update final_answer for a row in submission.json"
    )
    parser.add_argument("row_index", type=int, help="Row index (0-indexed)")
    parser.add_argument("answer", type=str, help="SQL query or 'null' for unanswerable")
    args = parser.parse_args()

    submission_path = Path("/workspace/submission.json")
    submission = json.loads(submission_path.read_text())

    if args.row_index < 0 or args.row_index >= len(submission):
        print(f"Error: row_index {args.row_index} out of range (0-{len(submission)-1})", file=sys.stderr)
        sys.exit(1)

    submission[args.row_index]["final_answer"] = args.answer
    submission_path.write_text(json.dumps(submission, indent=2))

    # Show progress
    answered = sum(1 for task in submission if task.get("final_answer", "").strip())
    total = len(submission)
    percent = round(100.0 * answered / total, 1)
    print(f"✓ Row {args.row_index} updated | Progress: {answered}/{total} ({percent}%)")


if __name__ == "__main__":
    main()
