#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import neighbor_tiles


def main() -> None:
    parser = argparse.ArgumentParser(description="List neighboring grid tiles around a seed tile.")
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    parser.add_argument("--radius", type=int, default=1)
    args = parser.parse_args()
    print(
        json.dumps(
            {
                "tiles": neighbor_tiles(args.x, args.y, radius=args.radius),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
