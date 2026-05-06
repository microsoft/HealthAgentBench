#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import read_region, save_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a rectangular region in grid-tile units.")
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    parser.add_argument("--width", type=int, default=2)
    parser.add_argument("--height", type=int, default=2)
    parser.add_argument("--max-size", type=int, default=2048)
    args = parser.parse_args()

    image = read_region(
        args.x,
        args.y,
        args.width,
        args.height,
        max_output_size=args.max_size,
    )
    path = save_image(image, f"region_{args.x}_{args.y}_{args.width}_{args.height}")
    print(
        json.dumps(
            {
                "image_path": str(path),
                "x": args.x,
                "y": args.y,
                "width_tiles": args.width,
                "height_tiles": args.height,
                "rendered_width": image.width,
                "rendered_height": image.height,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
