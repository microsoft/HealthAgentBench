#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.pathology_common import compute_tissue_mask, read_thumbnail, save_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute a heuristic tissue mask on the slide thumbnail.")
    parser.add_argument("--max-size", type=int, default=1024)
    args = parser.parse_args()

    thumb = read_thumbnail(max_size=args.max_size)
    mask, mask_img = compute_tissue_mask(thumb)
    path = save_image(mask_img, "tissue_mask")
    print(
        json.dumps(
            {
                "image_path": str(path),
                "thumbnail_width": thumb.width,
                "thumbnail_height": thumb.height,
                "tissue_fraction": round(float(mask.mean()), 6),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
