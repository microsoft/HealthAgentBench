#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import topk_attention_tiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Return the top-k tiles by cached GigaPath saliency score.")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--max-tiles", type=int, default=256)
    args = parser.parse_args()
    print(
        json.dumps(
            topk_attention_tiles(k=args.k, max_tiles=args.max_tiles),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
