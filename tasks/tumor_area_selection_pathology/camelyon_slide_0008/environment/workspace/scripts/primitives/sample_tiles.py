#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import sample_tissue_tiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample tissue-containing grid tiles from the current slide.")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-tissue-fraction", type=float, default=0.2)
    args = parser.parse_args()
    print(
        json.dumps(
            {
                "tiles": sample_tissue_tiles(
                    args.count,
                    seed=args.seed,
                    min_fraction=args.min_tissue_fraction,
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
