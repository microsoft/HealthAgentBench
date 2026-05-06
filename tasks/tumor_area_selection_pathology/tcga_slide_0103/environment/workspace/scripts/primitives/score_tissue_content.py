#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import tissue_fraction_for_tile


def main() -> None:
    parser = argparse.ArgumentParser(description="Score how much tissue appears in one grid tile.")
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            {
                "x": args.x,
                "y": args.y,
                "tissue_fraction": round(tissue_fraction_for_tile(args.x, args.y), 6),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
