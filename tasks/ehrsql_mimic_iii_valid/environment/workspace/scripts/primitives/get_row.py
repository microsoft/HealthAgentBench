#!/usr/bin/env python3
"""Get a row from submission.json by index (0-indexed)."""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Get a row from submission.json by index (0-indexed)"
    )
    parser.add_argument("row_index", type=int, help="Row index (0-indexed)")
    args = parser.parse_args()

    submission_path = Path("/workspace/submission.json")
    submission = json.loads(submission_path.read_text())

    if args.row_index < 0 or args.row_index >= len(submission):
        print(f"Error: row_index {args.row_index} out of range (0-{len(submission)-1})", file=sys.stderr)
        sys.exit(1)

    row = submission[args.row_index]
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
