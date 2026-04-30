#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import gigapath_heatmap_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or load a GigaPath-derived saliency map.")
    parser.add_argument("--max-size", type=int, default=1024)
    parser.add_argument("--max-tiles", type=int, default=256)
    args = parser.parse_args()
    payload, image_path = gigapath_heatmap_image(
        max_size=args.max_size,
        max_tiles=args.max_tiles,
    )
    payload = dict(payload)
    payload["image_path"] = str(image_path)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
