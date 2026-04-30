#!/usr/bin/env python3
"""Render tumor-area-selection ground-truth mask and tile overlays for benchmark inspection."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import tifffile
from PIL import Image, ImageDraw, ImageFont


BENCHMARK_NAME = "tumor_area_selection_pathology"
DEFAULT_TASK_ROOT = Path.home() / "code" / "MedCLI" / "tasks" / BENCHMARK_NAME
DEFAULT_CACHE_ROOT = Path.home() / "harbor-cache" / BENCHMARK_NAME
DEFAULT_OUTPUT_ROOT = Path.home() / "harbor-results" / f"{BENCHMARK_NAME}-camelyon-ground-truth"


@dataclass
class CamelyonTask:
    task_id: str
    source_slide_name: str
    tile_size: int
    analysis_downsample: int
    tumor_threshold: float
    expected_tumor_tiles: set[tuple[int, int]]
    mask_path: Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, default=DEFAULT_TASK_ROOT)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--thumbnail-size", type=int, default=1024)
    return parser.parse_args()


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _tile_set(value: Any) -> set[tuple[int, int]]:
    if not isinstance(value, list):
        return set()
    tiles: set[tuple[int, int]] = set()
    for row in value:
        if not isinstance(row, dict):
            continue
        x = row.get("x")
        y = row.get("y")
        if isinstance(x, int) and isinstance(y, int):
            tiles.add((x, y))
    return tiles


def _font_bbox(draw: ImageDraw.ImageDraw, pos: tuple[int, int], text: str, font: ImageFont.ImageFont) -> int:
    return draw.textbbox(pos, text, font=font)[3]


def _best_mask_page(mask_path: Path, max_size: int) -> np.ndarray:
    with tifffile.TiffFile(mask_path) as tif:
        best_page = tif.pages[0]
        best_score = abs(max(best_page.imagewidth, best_page.imagelength) - max_size)
        for page in tif.pages:
            score = abs(max(page.imagewidth, page.imagelength) - max_size)
            if score < best_score:
                best_page = page
                best_score = score
        mask = best_page.asarray()
    if getattr(mask, "ndim", 0) > 2:
        mask = mask[..., 0]
    return np.asarray(mask, dtype=np.uint8)


def _mask_panels(mask: np.ndarray) -> tuple[Image.Image, Image.Image]:
    h, w = mask.shape
    tissue = mask > 0
    tumor = mask == 2

    base = np.full((h, w, 3), 255, dtype=np.uint8)
    base[tissue] = (225, 225, 225)

    pixel = base.copy()
    pixel[tumor] = (220, 20, 60)

    return (
        Image.fromarray(base, mode="RGB"),
        Image.fromarray(pixel, mode="RGB"),
    )


def _tile_bbox(
    tile: tuple[int, int],
    tile_size: int,
    analysis_downsample: int,
    full_size: tuple[int, int],
    image_size: tuple[int, int],
) -> tuple[float, float, float, float]:
    full_w, full_h = full_size
    img_w, img_h = image_size
    x, y = tile
    x0 = x * tile_size * analysis_downsample
    y0 = y * tile_size * analysis_downsample
    x1 = x0 + tile_size * analysis_downsample
    y1 = y0 + tile_size * analysis_downsample
    sx = img_w / max(full_w, 1)
    sy = img_h / max(full_h, 1)
    return x0 * sx, y0 * sy, x1 * sx, y1 * sy


def _draw_tile_overlay(
    base: Image.Image,
    tiles: set[tuple[int, int]],
    tile_size: int,
    analysis_downsample: int,
    full_size: tuple[int, int],
) -> Image.Image:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for tile in sorted(tiles):
        x0, y0, x1, y1 = _tile_bbox(
            tile,
            tile_size,
            analysis_downsample,
            full_size,
            base.size,
        )
        draw.rectangle((x0, y0, x1, y1), fill=(255, 191, 0, 96), outline=(153, 102, 0, 255), width=2)
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def _render_panel(task: CamelyonTask, thumbnail_size: int) -> Image.Image:
    mask = _best_mask_page(task.mask_path, thumbnail_size)
    full_h, full_w = mask.shape
    base_panel, pixel_panel = _mask_panels(mask)
    tile_panel = _draw_tile_overlay(
        base_panel,
        task.expected_tumor_tiles,
        task.tile_size,
        task.analysis_downsample,
        (full_w, full_h),
    )
    combined_panel = _draw_tile_overlay(
        pixel_panel,
        task.expected_tumor_tiles,
        task.tile_size,
        task.analysis_downsample,
        (full_w, full_h),
    )

    title_font = _font(26)
    body_font = _font(18)
    padding = 16
    gap = 18
    labels = [
        ("Mask background", base_panel),
        ("Pixel-level tumor mask", pixel_panel),
        ("20% tile ground truth", tile_panel),
        ("Combined mask + tiles", combined_panel),
    ]
    img_h = base_panel.height
    img_w = base_panel.width
    text_w = 420
    canvas_w = padding * 2 + (img_w * len(labels)) + gap * (len(labels) - 1) + text_w + gap
    canvas_h = padding * 2 + img_h + 40
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    x = padding
    for label, panel in labels:
        canvas.paste(panel, (x, padding))
        draw.text((x, padding + img_h + 8), label, fill=(0, 0, 0), font=body_font)
        x += img_w + gap

    text_x = x
    lines = [
        task.task_id,
        f"Source slide: {task.source_slide_name}",
        f"Positive tiles: {len(task.expected_tumor_tiles)}",
        f"Tumor threshold: {task.tumor_threshold:.2f}",
        f"Tile size: {task.tile_size}",
        f"Analysis downsample: {task.analysis_downsample}",
        f"Mask display size: {full_w} x {full_h}",
    ]
    y = padding
    for index, line in enumerate(lines):
        font = title_font if index == 0 else body_font
        color = (0, 0, 0) if index < 2 else (80, 80, 80)
        draw.text((text_x, y), line, fill=color, font=font)
        y = _font_bbox(draw, (text_x, y), line, font) + 10
    return canvas


def _load_tasks(task_root: Path, cache_root: Path) -> list[CamelyonTask]:
    tasks: list[CamelyonTask] = []
    for task_dir in sorted(task_root.glob("camelyon_slide_*")):
        answer_key = _load_json(task_dir / "tests" / "task_answer_key.json")[0]
        source_slide_name = str(answer_key["source_slide_name"])
        tasks.append(
            CamelyonTask(
                task_id=str(answer_key["task_id"]),
                source_slide_name=source_slide_name,
                tile_size=int(answer_key["tile_size"]),
                analysis_downsample=int(answer_key["analysis_downsample"]),
                tumor_threshold=float(answer_key["tumor_threshold"]),
                expected_tumor_tiles=_tile_set(answer_key.get("expected_tumor_tiles")),
                mask_path=cache_root / "camelyon16" / "masks" / f"{source_slide_name}_mask.tif",
            )
        )
    return tasks


def _write_index(output_dir: Path, summaries: list[dict[str, Any]]) -> None:
    cards = []
    for row in summaries:
        cards.append(
            "<div class='card'>"
            f"<h3>{row['task_id']}</h3>"
            f"<p>{row['source_slide_name']} | positive tiles: {row['positive_tiles']}</p>"
            f"<img src='{row['image']}' alt='{row['task_id']}' />"
            "</div>"
        )
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Tumor Area Selection Ground Truth</title>"
        "<style>body{font-family:Arial,sans-serif;margin:24px;background:#fafafa}"
        ".card{background:white;border:1px solid #ddd;padding:16px;margin:16px 0}"
        "img{max-width:100%;height:auto;border:1px solid #ccc}</style></head><body>"
        "<h1>Tumor Area Selection Ground Truth Gallery</h1>"
        "<p>Each panel shows the mask background, pixel-level tumor mask, the derived 20% tile-level ground truth, and a combined overlay.</p>"
        + "".join(cards)
        + "</body></html>"
    )
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tasks = _load_tasks(args.task_root, args.cache_root)
    summaries: list[dict[str, Any]] = []
    for task in tasks:
        if not task.mask_path.exists():
            raise FileNotFoundError(f"Missing mask file: {task.mask_path}")
        image_name = f"{task.task_id}_ground_truth.png"
        panel = _render_panel(task, args.thumbnail_size)
        panel.save(args.output_dir / image_name)
        summaries.append(
            {
                "task_id": task.task_id,
                "source_slide_name": task.source_slide_name,
                "positive_tiles": len(task.expected_tumor_tiles),
                "tumor_threshold": task.tumor_threshold,
                "image": image_name,
            }
        )
    (args.output_dir / "summary.json").write_text(
        json.dumps(summaries, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_index(args.output_dir, summaries)
    print(json.dumps({"task_count": len(tasks), "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
