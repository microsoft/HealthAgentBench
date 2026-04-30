#!/usr/bin/env python3
"""Generate visual error analysis artifacts for tumor_area_selection_pathology runs."""

from __future__ import annotations

import argparse
import html
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tifffile
from PIL import Image, ImageColor, ImageDraw, ImageFont


try:
    import openslide
except Exception:  # pragma: no cover - fallback is supported
    openslide = None


BENCHMARK_NAME = "tumor_area_selection_pathology"
DEFAULT_CACHE_ROOT = Path.home() / "harbor-cache" / BENCHMARK_NAME
DEFAULT_TASK_ROOT = Path.home() / "code" / "MedCLI" / "tasks" / BENCHMARK_NAME
DEFAULT_OUTPUT_ROOT = Path.home() / "harbor-results" / f"{BENCHMARK_NAME}-visual-analysis"


@dataclass
class TrialArtifact:
    task_id: str
    trial_id: str
    trial_dir: Path
    submission: dict[str, Any]
    error_analysis: dict[str, Any]
    answer_key: dict[str, Any]
    task_manifest: dict[str, Any]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result-dir",
        action="append",
        dest="result_dirs",
        required=True,
        help="Harbor result directory. May be provided multiple times.",
    )
    parser.add_argument(
        "--task-root",
        type=Path,
        default=DEFAULT_TASK_ROOT,
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=DEFAULT_CACHE_ROOT,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument(
        "--thumbnail-size",
        type=int,
        default=1024,
    )
    parser.add_argument(
        "--patch-size",
        type=int,
        default=160,
    )
    parser.add_argument(
        "--skip-patch-sheets",
        action="store_true",
        help="Skip CAMELYON patch-sheet generation and only render overlays/galleries.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


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


def _outcome_color(outcome: str) -> tuple[int, int, int]:
    palette = {
        "TP": (44, 160, 44),
        "TN": (31, 119, 180),
        "FP": (214, 39, 40),
        "FN": (255, 140, 0),
    }
    return palette.get(outcome, (90, 90, 90))


def _open_dimensions(slide_path: Path) -> tuple[int, int]:
    if openslide is not None and slide_path.suffix.lower() in {".svs", ".tif", ".tiff"}:
        try:
            with openslide.OpenSlide(str(slide_path)) as slide:
                width, height = slide.dimensions
                return int(width), int(height)
        except Exception:
            pass
    with tifffile.TiffFile(slide_path) as tif:
        page = tif.pages[0]
        return int(page.imagewidth), int(page.imagelength)


def _best_tiff_page(
    tif: tifffile.TiffFile,
    desired_downsample: float,
) -> tuple[Any, float]:
    base_page = tif.pages[0]
    base_width = max(int(base_page.imagewidth), 1)
    best_page = base_page
    best_downsample = 1.0
    best_score = abs(best_downsample - desired_downsample)
    for page in tif.pages:
        page_width = max(int(page.imagewidth), 1)
        page_downsample = base_width / page_width
        score = abs(page_downsample - desired_downsample)
        if score < best_score:
            best_page = page
            best_downsample = page_downsample
            best_score = score
    return best_page, best_downsample


def _read_thumbnail(slide_path: Path, max_size: int) -> Image.Image:
    if openslide is not None:
        try:
            with openslide.OpenSlide(str(slide_path)) as slide:
                return slide.get_thumbnail((max_size, max_size)).convert("RGB")
        except Exception:
            pass
    with tifffile.TiffFile(slide_path) as tif:
        desired_downsample = max(_open_dimensions(slide_path)) / max(max_size, 1)
        page, _ = _best_tiff_page(tif, max(desired_downsample, 1.0))
        arr = page.asarray()
    if getattr(arr, "ndim", 0) == 2:
        arr = arr[..., None].repeat(3, axis=2)
    image = Image.fromarray(arr.astype("uint8")).convert("RGB")
    image.thumbnail((max_size, max_size))
    return image


def _read_grid_tile(
    slide_path: Path,
    x: int,
    y: int,
    tile_size: int,
    analysis_downsample: int,
    out_size: int,
) -> Image.Image:
    x0 = int(x * tile_size * analysis_downsample)
    y0 = int(y * tile_size * analysis_downsample)
    source_w = max(tile_size * analysis_downsample, 1)
    source_h = max(tile_size * analysis_downsample, 1)
    if openslide is not None:
        try:
            with openslide.OpenSlide(str(slide_path)) as slide:
                desired_downsample = float(analysis_downsample)
                level = int(slide.get_best_level_for_downsample(desired_downsample))
                level_downsample = float(slide.level_downsamples[level])
                level_width = max(int(math.ceil(source_w / level_downsample)), 1)
                level_height = max(int(math.ceil(source_h / level_downsample)), 1)
                image = slide.read_region((x0, y0), level, (level_width, level_height)).convert("RGB")
                if image.size != (out_size, out_size):
                    image = image.resize((out_size, out_size), Image.Resampling.BILINEAR)
                return image
        except Exception:
            pass
    with tifffile.TiffFile(slide_path) as tif:
        page, page_downsample = _best_tiff_page(tif, float(analysis_downsample))
        arr = page.asarray()
    if getattr(arr, "ndim", 0) == 2:
        arr = arr[..., None].repeat(3, axis=2)
    page_x0 = max(int(math.floor(x0 / page_downsample)), 0)
    page_y0 = max(int(math.floor(y0 / page_downsample)), 0)
    page_x1 = min(max(int(math.ceil((x0 + source_w) / page_downsample)), page_x0 + 1), arr.shape[1])
    page_y1 = min(max(int(math.ceil((y0 + source_h) / page_downsample)), page_y0 + 1), arr.shape[0])
    patch = arr[page_y0:page_y1, page_x0:page_x1]
    if patch.size == 0:
        patch = Image.new("RGB", (1, 1), "black")
    else:
        patch = Image.fromarray(patch.astype("uint8")).convert("RGB")
    if patch.size != (out_size, out_size):
        patch = patch.resize((out_size, out_size), Image.Resampling.BILINEAR)
    return patch


def _locate_slide(cache_root: Path, trial: TrialArtifact) -> Path:
    subset = str(trial.answer_key.get("subset", ""))
    if subset == "tcga":
        source_file_id = str(trial.task_manifest["source_file_id"])
        slide_extension = str(trial.task_manifest.get("slide_extension", ".svs"))
        return cache_root / "tcga" / f"{source_file_id}{slide_extension}"
    if subset == "camelyon16":
        source_name = str(trial.task_manifest["source_slide_name"])
        return cache_root / "camelyon16" / "slides" / f"{source_name}.tif"
    raise ValueError(f"Unknown subset: {subset}")


def _render_text_panel(
    lines: list[tuple[str, tuple[int, int, int]]],
    width: int,
    min_height: int,
) -> Image.Image:
    title_font = _font(28)
    body_font = _font(22)
    padding = 24
    line_gap = 10
    panel = Image.new("RGB", (width, min_height), "white")
    draw = ImageDraw.Draw(panel)
    y = padding
    for index, (text, color) in enumerate(lines):
        font = title_font if index == 0 else body_font
        draw.text((padding, y), text, fill=color, font=font)
        bbox = draw.textbbox((padding, y), text, font=font)
        y = bbox[3] + line_gap
    return panel


def _tcga_outcome(expected: bool, predicted: bool) -> str:
    if predicted and expected:
        return "TP"
    if (not predicted) and (not expected):
        return "TN"
    if predicted and (not expected):
        return "FP"
    return "FN"


def _render_tcga_case(
    trial: TrialArtifact,
    slide_path: Path,
    output_path: Path,
    thumbnail_size: int,
) -> dict[str, Any]:
    expected = _bool(trial.answer_key.get("expected_contains_tumor"))
    predicted = _bool(trial.submission.get("contains_tumor"))
    outcome = _tcga_outcome(expected, predicted)
    color = _outcome_color(outcome)
    thumb = _read_thumbnail(slide_path, thumbnail_size)

    bordered = Image.new("RGB", (thumb.width + 24, thumb.height + 24), color)
    bordered.paste(thumb, (12, 12))
    lines = [
        (trial.task_id, (0, 0, 0)),
        (f"Outcome: {outcome}", color),
        (f"Ground truth: {'tumor' if expected else 'normal'}", (0, 0, 0)),
        (f"Predicted: {'tumor' if predicted else 'normal'}", (0, 0, 0)),
        (f"Source label: {trial.answer_key.get('source_label_name', 'unknown')}", (80, 80, 80)),
        (f"Trial dir: {trial.trial_dir.name}", (80, 80, 80)),
    ]
    panel = _render_text_panel(lines, 420, bordered.height)
    canvas = Image.new("RGB", (bordered.width + panel.width, max(bordered.height, panel.height)), "white")
    canvas.paste(bordered, (0, 0))
    canvas.paste(panel, (bordered.width, 0))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)

    return {
        "subset": "tcga",
        "task_id": trial.task_id,
        "outcome": outcome,
        "expected": expected,
        "predicted": predicted,
        "image": output_path.name,
        "trial_dir": str(trial.trial_dir),
    }


def _tile_bbox_on_thumbnail(
    tile: tuple[int, int],
    tile_size: int,
    analysis_downsample: int,
    slide_size: tuple[int, int],
    thumb_size: tuple[int, int],
) -> tuple[float, float, float, float]:
    slide_w, slide_h = slide_size
    thumb_w, thumb_h = thumb_size
    x, y = tile
    x0 = x * tile_size * analysis_downsample
    y0 = y * tile_size * analysis_downsample
    x1 = x0 + tile_size * analysis_downsample
    y1 = y0 + tile_size * analysis_downsample
    sx = thumb_w / slide_w
    sy = thumb_h / slide_h
    return x0 * sx, y0 * sy, x1 * sx, y1 * sy


def _draw_tile_overlays(
    base: Image.Image,
    tp_tiles: set[tuple[int, int]],
    fp_tiles: set[tuple[int, int]],
    fn_tiles: set[tuple[int, int]],
    tile_size: int,
    analysis_downsample: int,
    slide_size: tuple[int, int],
) -> Image.Image:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    def draw_tiles(
        tiles: set[tuple[int, int]],
        fill: tuple[int, int, int, int],
        outline: tuple[int, int, int, int],
    ) -> None:
        for tile in sorted(tiles):
            x0, y0, x1, y1 = _tile_bbox_on_thumbnail(
                tile,
                tile_size,
                analysis_downsample,
                slide_size,
                base.size,
            )
            draw.rectangle((x0, y0, x1, y1), fill=fill, outline=outline, width=2)

    draw_tiles(fn_tiles, (255, 191, 0, 92), (153, 102, 0, 255))
    draw_tiles(tp_tiles, (44, 160, 44, 120), (0, 110, 0, 255))
    draw_tiles(fp_tiles, (214, 39, 40, 120), (120, 0, 0, 255))
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def _draw_positive_tile_overlay(
    base: Image.Image,
    tiles: set[tuple[int, int]],
    tile_size: int,
    analysis_downsample: int,
    slide_size: tuple[int, int],
    *,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
) -> Image.Image:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for tile in sorted(tiles):
        x0, y0, x1, y1 = _tile_bbox_on_thumbnail(
            tile,
            tile_size,
            analysis_downsample,
            slide_size,
            base.size,
        )
        draw.rectangle((x0, y0, x1, y1), fill=fill, outline=outline, width=2)
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def _labeled_image(image: Image.Image, label: str) -> Image.Image:
    padding = 16
    title_h = 48
    canvas = Image.new("RGB", (image.width, image.height + title_h + padding), "white")
    canvas.paste(image, (0, title_h + padding))
    draw = ImageDraw.Draw(canvas)
    draw.text((padding, 12), label, fill=(0, 0, 0), font=_font(24))
    return canvas


def _render_camelyon_compare_panel(
    base: Image.Image,
    predicted_tiles: set[tuple[int, int]],
    gold_tiles: set[tuple[int, int]],
    tile_size: int,
    analysis_downsample: int,
    slide_size: tuple[int, int],
) -> Image.Image:
    predicted = _draw_positive_tile_overlay(
        base,
        predicted_tiles,
        tile_size,
        analysis_downsample,
        slide_size,
        fill=(31, 119, 180, 120),
        outline=(12, 60, 120, 255),
    )
    gold = _draw_positive_tile_overlay(
        base,
        gold_tiles,
        tile_size,
        analysis_downsample,
        slide_size,
        fill=(44, 160, 44, 120),
        outline=(0, 110, 0, 255),
    )
    predicted = _labeled_image(predicted, "Prediction")
    gold = _labeled_image(gold, "Ground Truth")
    gap = 20
    canvas = Image.new("RGB", (predicted.width + gold.width + gap, max(predicted.height, gold.height)), "white")
    canvas.paste(predicted, (0, 0))
    canvas.paste(gold, (predicted.width + gap, 0))
    return canvas


def _render_tile_patch_sheet(
    slide_path: Path,
    tile_size: int,
    analysis_downsample: int,
    tp_tiles: set[tuple[int, int]],
    fp_tiles: set[tuple[int, int]],
    fn_tiles: set[tuple[int, int]],
    output_path: Path,
    patch_size: int,
) -> Path:
    sections = [
        ("True positives", (44, 160, 44), sorted(tp_tiles)[:12]),
        ("False positives", (214, 39, 40), sorted(fp_tiles)[:12]),
        ("False negatives", (255, 140, 0), sorted(fn_tiles)[:12]),
    ]
    title_font = _font(26)
    body_font = _font(18)
    padding = 20
    cols = 4
    patch_card_w = patch_size + 24
    patch_card_h = patch_size + 42
    section_gap = 24

    section_heights: list[int] = []
    for _title, _color, tiles in sections:
        rows = max(1, math.ceil(max(len(tiles), 1) / cols))
        section_heights.append(48 + rows * patch_card_h)

    canvas_w = padding * 2 + cols * patch_card_w
    canvas_h = padding * 2 + sum(section_heights) + section_gap * (len(sections) - 1)
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)
    y = padding
    for title, color, tiles in sections:
        draw.text((padding, y), title, fill=color, font=title_font)
        y += 40
        if not tiles:
            draw.text((padding, y), "None", fill=(90, 90, 90), font=body_font)
            y += patch_card_h
        else:
            for idx, tile in enumerate(tiles):
                col = idx % cols
                row = idx // cols
                x = padding + col * patch_card_w
                yy = y + row * patch_card_h
                patch = _read_grid_tile(
                    slide_path,
                    tile[0],
                    tile[1],
                    tile_size,
                    analysis_downsample,
                    patch_size,
                )
                canvas.paste(patch, (x, yy))
                draw.rectangle((x, yy, x + patch_size, yy + patch_size), outline=color, width=3)
                draw.text((x, yy + patch_size + 6), f"({tile[0]}, {tile[1]})", fill=(0, 0, 0), font=body_font)
            rows = math.ceil(len(tiles) / cols)
            y += rows * patch_card_h
        y += section_gap
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return output_path


def _render_camelyon_case(
    trial: TrialArtifact,
    compare_path: Path,
    slide_path: Path,
    overlay_path: Path,
    patch_sheet_path: Path,
    thumbnail_size: int,
    patch_size: int,
    skip_patch_sheets: bool,
) -> dict[str, Any]:
    predicted_tiles = _tile_set(trial.submission.get("predicted_tumor_tiles"))
    gold_tiles = _tile_set(trial.answer_key.get("expected_tumor_tiles"))
    tp_tiles = predicted_tiles & gold_tiles
    fp_tiles = predicted_tiles - gold_tiles
    fn_tiles = gold_tiles - predicted_tiles
    tile_precision = float(trial.error_analysis.get("tile_precision", 0.0))
    tile_recall = float(trial.error_analysis.get("tile_recall", 0.0))
    tile_f1 = float(trial.error_analysis.get("tile_f1", 0.0))
    tumor_coverage = float(trial.error_analysis.get("tumor_coverage", 0.0))

    thumb = _read_thumbnail(slide_path, thumbnail_size)
    slide_size = _open_dimensions(slide_path)
    tile_size = int(trial.answer_key.get("tile_size", trial.task_manifest.get("tile_size", 256)))
    analysis_downsample = int(
        trial.answer_key.get("analysis_downsample", trial.task_manifest.get("analysis_downsample", 16))
    )
    overlay = _draw_tile_overlays(
        thumb,
        tp_tiles,
        fp_tiles,
        fn_tiles,
        tile_size,
        analysis_downsample,
        slide_size,
    )
    compare_panel = _render_camelyon_compare_panel(
        thumb,
        predicted_tiles,
        gold_tiles,
        tile_size,
        analysis_downsample,
        slide_size,
    )
    compare_path.parent.mkdir(parents=True, exist_ok=True)
    compare_panel.save(compare_path)
    lines = [
        (trial.task_id, (0, 0, 0)),
        (f"Tile F1: {tile_f1:.3f}", (0, 0, 0)),
        (f"Precision: {tile_precision:.3f}", (44, 160, 44)),
        (f"Recall: {tile_recall:.3f}", (255, 140, 0)),
        (f"Tumor coverage: {tumor_coverage:.3f}", (148, 103, 189)),
        (f"Predicted tiles: {len(predicted_tiles)}", (0, 0, 0)),
        (f"Gold tumor tiles: {len(gold_tiles)}", (0, 0, 0)),
        (f"TP: {len(tp_tiles)}", (44, 160, 44)),
        (f"FP: {len(fp_tiles)}", (214, 39, 40)),
        (f"FN: {len(fn_tiles)}", (255, 140, 0)),
        (f"Source slide: {trial.task_manifest.get('source_slide_name', 'unknown')}", (80, 80, 80)),
    ]
    panel = _render_text_panel(lines, 420, overlay.height)
    canvas = Image.new("RGB", (overlay.width + panel.width, max(overlay.height, panel.height)), "white")
    canvas.paste(overlay, (0, 0))
    canvas.paste(panel, (overlay.width, 0))
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(overlay_path)

    patch_image_name: str | None = None
    if not skip_patch_sheets:
        try:
            _render_tile_patch_sheet(
                slide_path,
                tile_size,
                analysis_downsample,
                tp_tiles,
                fp_tiles,
                fn_tiles,
                patch_sheet_path,
                patch_size,
            )
            patch_image_name = patch_sheet_path.name
        except Exception:
            patch_image_name = None

    return {
        "subset": "camelyon16",
        "task_id": trial.task_id,
        "tile_precision": round(tile_precision, 4),
        "tile_recall": round(tile_recall, 4),
        "tile_f1": round(tile_f1, 4),
        "tumor_coverage": round(tumor_coverage, 4),
        "tp": len(tp_tiles),
        "fp": len(fp_tiles),
        "fn": len(fn_tiles),
        "compare_image": compare_path.name,
        "overlay_image": overlay_path.name,
        "patch_image": patch_image_name,
        "trial_dir": str(trial.trial_dir),
    }


def _collect_trials(result_dirs: list[Path], task_root: Path) -> list[TrialArtifact]:
    trials: dict[str, TrialArtifact] = {}
    for result_dir in result_dirs:
        for child in sorted(result_dir.iterdir()):
            if not child.is_dir():
                continue
            submission_path = child / "artifacts" / "submission.json"
            error_path = child / "artifacts" / "error_analysis.json"
            result_path = child / "result.json"
            if not (submission_path.exists() and error_path.exists() and result_path.exists()):
                continue
            task_id = child.name.split("__", 1)[0]
            if task_id in trials:
                raise ValueError(f"Duplicate task_id across result dirs: {task_id}")
            task_dir = task_root / task_id
            answer_key = _load_json(task_dir / "tests" / "task_answer_key.json")[0]
            task_manifest = _load_json(task_dir / "environment" / "task_manifest.json")
            submission = _load_json(submission_path)[0]
            error_analysis = _load_json(error_path)[0]
            trials[task_id] = TrialArtifact(
                task_id=task_id,
                trial_id=child.name,
                trial_dir=child,
                submission=submission,
                error_analysis=error_analysis,
                answer_key=answer_key,
                task_manifest=task_manifest,
            )
    return [trials[key] for key in sorted(trials)]


def _safe_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _gallery_image(
    image_entries: list[tuple[str, Path, str]],
    output_path: Path,
    thumb_w: int = 420,
) -> Path:
    if not image_entries:
        return output_path
    font = _font(20)
    padding = 18
    label_h = 64
    cols = 2
    loaded: list[tuple[str, Image.Image, str]] = []
    max_h = 0
    for label, path, subtitle in image_entries:
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, 720))
        loaded.append((label, image, subtitle))
        max_h = max(max_h, image.height)
    card_h = max_h + label_h
    rows = math.ceil(len(loaded) / cols)
    canvas = Image.new(
        "RGB",
        (padding * 2 + cols * thumb_w + (cols - 1) * padding, padding * 2 + rows * card_h + (rows - 1) * padding),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for idx, (label, image, subtitle) in enumerate(loaded):
        col = idx % cols
        row = idx // cols
        x = padding + col * (thumb_w + padding)
        y = padding + row * (card_h + padding)
        canvas.paste(image, (x, y))
        draw.text((x, y + max_h + 6), label, fill=(0, 0, 0), font=font)
        draw.text((x, y + max_h + 32), subtitle, fill=(90, 90, 90), font=_font(16))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return output_path


def _metric_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    tcga_tp = sum(1 for row in rows if row["subset"] == "tcga" and row.get("outcome") == "TP")
    tcga_fp = sum(1 for row in rows if row["subset"] == "tcga" and row.get("outcome") == "FP")
    tcga_fn = sum(1 for row in rows if row["subset"] == "tcga" and row.get("outcome") == "FN")
    tcga_tn = sum(1 for row in rows if row["subset"] == "tcga" and row.get("outcome") == "TN")
    cam_tp = sum(int(row.get("tp", 0)) for row in rows if row["subset"] == "camelyon16")
    cam_fp = sum(int(row.get("fp", 0)) for row in rows if row["subset"] == "camelyon16")
    cam_fn = sum(int(row.get("fn", 0)) for row in rows if row["subset"] == "camelyon16")

    tcga_precision = tcga_tp / (tcga_tp + tcga_fp) if (tcga_tp + tcga_fp) else 0.0
    tcga_recall = tcga_tp / (tcga_tp + tcga_fn) if (tcga_tp + tcga_fn) else 0.0
    tcga_f1 = (
        2 * tcga_precision * tcga_recall / (tcga_precision + tcga_recall)
        if (tcga_precision + tcga_recall)
        else 0.0
    )
    tcga_accuracy = (
        (tcga_tp + tcga_tn) / (tcga_tp + tcga_tn + tcga_fp + tcga_fn)
        if (tcga_tp + tcga_tn + tcga_fp + tcga_fn)
        else 0.0
    )
    cam_precision = cam_tp / (cam_tp + cam_fp) if (cam_tp + cam_fp) else 0.0
    cam_recall = cam_tp / (cam_tp + cam_fn) if (cam_tp + cam_fn) else 0.0
    cam_f1 = (
        2 * cam_precision * cam_recall / (cam_precision + cam_recall)
        if (cam_precision + cam_recall)
        else 0.0
    )
    return {
        "tcga_slide_precision": round(tcga_precision, 4),
        "tcga_slide_recall": round(tcga_recall, 4),
        "tcga_slide_f1": round(tcga_f1, 4),
        "tcga_slide_accuracy": round(tcga_accuracy, 4),
        "camelyon_tile_precision": round(cam_precision, 4),
        "camelyon_tile_recall": round(cam_recall, 4),
        "camelyon_tile_f1": round(cam_f1, 4),
        "camelyon_tumor_coverage": round(
            (
                sum(float(row.get("tumor_coverage", 0.0)) for row in rows if row["subset"] == "camelyon16")
                / max(1, sum(1 for row in rows if row["subset"] == "camelyon16"))
            ),
            4,
        ),
        "tcga_tp": tcga_tp,
        "tcga_fp": tcga_fp,
        "tcga_fn": tcga_fn,
        "tcga_tn": tcga_tn,
        "cam_tp": cam_tp,
        "cam_fp": cam_fp,
        "cam_fn": cam_fn,
    }


def _write_index(
    output_dir: Path,
    rows: list[dict[str, Any]],
    metrics: dict[str, float],
    tcga_gallery: Path,
    camelyon_gallery: Path,
) -> Path:
    tcga_rows = [row for row in rows if row["subset"] == "tcga"]
    cam_rows = [row for row in rows if row["subset"] == "camelyon16"]

    def outcome_rank(outcome: str) -> int:
        return {"FP": 0, "FN": 1, "TP": 2, "TN": 3}.get(outcome, 9)

    tcga_rows.sort(key=lambda row: (outcome_rank(str(row.get("outcome", ""))), str(row["task_id"])))
    cam_rows.sort(key=lambda row: (-float(row.get("tile_f1", 0.0)), str(row["task_id"])))

    lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        "<title>Tumor Area Selection Pathology Visual Error Analysis</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 24px; line-height: 1.4; }",
        "table { border-collapse: collapse; margin-bottom: 24px; }",
        "th, td { border: 1px solid #ccc; padding: 8px 10px; text-align: left; }",
        "img { max-width: 100%; height: auto; border: 1px solid #ddd; }",
        ".grid { display: grid; grid-template-columns: 1fr; gap: 20px; }",
        ".case { border: 1px solid #ddd; padding: 16px; border-radius: 8px; }",
        ".links a { margin-right: 16px; }",
        "</style></head><body>",
        "<h1>Tumor Area Selection Pathology Visual Error Analysis</h1>",
        "<p>The CAMELYON gallery shows prediction and ground-truth tumor-tile overlays side by side. Detailed case pages still include TP/FP/FN overlays and patch sheets.</p>",
        "<h2>Aggregate Metrics</h2>",
        "<table>",
        "<tr><th>Metric</th><th>Value</th></tr>",
    ]
    for key in [
        "tcga_slide_precision",
        "tcga_slide_recall",
        "tcga_slide_f1",
        "tcga_slide_accuracy",
        "camelyon_tile_precision",
        "camelyon_tile_recall",
        "camelyon_tile_f1",
        "camelyon_tumor_coverage",
    ]:
        lines.append(f"<tr><td>{html.escape(key)}</td><td>{metrics[key]}</td></tr>")
    lines.extend(
        [
            "</table>",
            "<h2>Gallery Overviews</h2>",
            f"<p><a href='{html.escape(_safe_rel(tcga_gallery, output_dir))}'>TCGA gallery</a> | "
            f"<a href='{html.escape(_safe_rel(camelyon_gallery, output_dir))}'>CAMELYON gallery</a></p>",
            "<h2>TCGA Slide-Level Cases</h2>",
            "<div class='grid'>",
        ]
    )
    for row in tcga_rows:
        lines.extend(
            [
                "<div class='case'>",
                f"<h3>{html.escape(row['task_id'])} - {html.escape(str(row['outcome']))}</h3>",
                f"<p>Ground truth: {'tumor' if row['expected'] else 'normal'} | "
                f"Predicted: {'tumor' if row['predicted'] else 'normal'}</p>",
                f"<p class='links'><a href='{html.escape(row['image'])}'>Open image</a></p>",
                f"<img src='{html.escape(row['image'])}' alt='{html.escape(row['task_id'])}'>",
                "</div>",
            ]
        )
    lines.extend(["</div>", "<h2>CAMELYON Tile-Level Cases</h2>", "<div class='grid'>"])
    for row in cam_rows:
        patch_link = (
            f" <a href='{html.escape(str(row['patch_image']))}'>Patch sheet</a>"
            if row.get("patch_image")
            else ""
        )
        lines.extend(
            [
                "<div class='case'>",
                f"<h3>{html.escape(row['task_id'])}</h3>",
                f"<p>F1: {row['tile_f1']:.4f} | Precision: {row['tile_precision']:.4f} | Recall: {row['tile_recall']:.4f}</p>",
                f"<p>Coverage: {row['tumor_coverage']:.4f} | TP: {row['tp']} | FP: {row['fp']} | FN: {row['fn']}</p>",
                f"<p class='links'><a href='{html.escape(row['compare_image'])}'>Prediction vs ground truth</a> "
                f"<a href='{html.escape(row['overlay_image'])}'>Detailed overlay</a> "
                f"{patch_link}</p>",
                f"<img src='{html.escape(row['compare_image'])}' alt='{html.escape(row['task_id'])} comparison'>",
                "</div>",
            ]
        )
    lines.extend(["</div>", "</body></html>"])
    index_path = output_dir / "index.html"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


def main() -> int:
    args = _parse_args()
    result_dirs = [Path(path).expanduser().resolve() for path in args.result_dirs]
    task_root = args.task_root.expanduser().resolve()
    cache_root = args.cache_root.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    trials = _collect_trials(result_dirs, task_root)
    rows: list[dict[str, Any]] = []
    tcga_gallery_inputs: list[tuple[str, Path, str]] = []
    camelyon_gallery_inputs: list[tuple[str, Path, str]] = []

    for trial in trials:
        slide_path = _locate_slide(cache_root, trial)
        if not slide_path.exists():
            raise FileNotFoundError(f"Missing slide cache for {trial.task_id}: {slide_path}")
        subset = str(trial.answer_key.get("subset", ""))
        if subset == "tcga":
            image_path = output_dir / f"{trial.task_id}.png"
            row = _render_tcga_case(trial, slide_path, image_path, args.thumbnail_size)
            tcga_gallery_inputs.append((trial.task_id, image_path, str(row["outcome"])))
        elif subset == "camelyon16":
            compare_path = output_dir / f"{trial.task_id}_compare.png"
            overlay_path = output_dir / f"{trial.task_id}_overlay.png"
            patch_path = output_dir / f"{trial.task_id}_patches.png"
            row = _render_camelyon_case(
                trial,
                compare_path,
                slide_path,
                overlay_path,
                patch_path,
                args.thumbnail_size,
                args.patch_size,
                args.skip_patch_sheets,
            )
            camelyon_gallery_inputs.append((trial.task_id, compare_path, f"F1 {row['tile_f1']:.3f}"))
        else:
            raise ValueError(f"Unknown subset: {subset}")
        rows.append(row)

    metrics = _metric_summary(rows)
    (output_dir / "summary.json").write_text(
        json.dumps({"metrics": metrics, "cases": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    tcga_gallery = _gallery_image(tcga_gallery_inputs, output_dir / "tcga_gallery.png")
    camelyon_gallery = _gallery_image(camelyon_gallery_inputs, output_dir / "camelyon_gallery.png")
    index_path = _write_index(output_dir, rows, metrics, tcga_gallery, camelyon_gallery)
    print(index_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
