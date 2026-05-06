#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import weak_tumor_probability


def main() -> None:
    parser = argparse.ArgumentParser(description="Return a weak heuristic probability that a tile contains tumor.")
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    args = parser.parse_args()
    payload = weak_tumor_probability(args.x, args.y)
    payload.update({"x": args.x, "y": args.y})
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
