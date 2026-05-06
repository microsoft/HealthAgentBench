#!/usr/bin/env python3
"""Verifier for tumor_area_selection_pathology Harbor tasks."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import requests
import tifffile

from harbor_evaluator import evaluate_submission_rows, load_submission_text


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, default=Path("/workspace/submission.json"))
    parser.add_argument("--answer-key", type=Path, default=Path("/tests/task_answer_key.json"))
    parser.add_argument("--reward-file", type=Path, default=Path("/logs/verifier/reward.txt"))
    parser.add_argument(
        "--reward-json", type=Path, default=Path("/logs/verifier/reward.json")
    )
    parser.add_argument(
        "--results-json", type=Path, default=Path("/logs/verifier/meta_results.json")
    )
    parser.add_argument(
        "--error-analysis-file",
        type=Path,
        default=Path("/logs/artifacts/error_analysis.json"),
    )
    parser.add_argument(
        "--slide-path",
        type=Path,
        default=Path("/data/slide/current"),
        help="Directory containing the materialized slide file and metadata.",
    )
    parser.add_argument(
        "--hidden-cache-root",
        type=Path,
        default=Path("/tmp/tumor_area_selection_pathology_verifier"),
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_tile_set(value: Any) -> set[tuple[int, int]]:
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


def _download_hidden_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            shutil.copyfileobj(response.raw, handle)
    return destination


def _materialized_slide_file(slide_dir: Path) -> Path:
    for candidate in sorted(slide_dir.glob("slide.*")):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No materialized slide file found under {slide_dir}")


def _open_slide_dimensions(slide_path: Path) -> tuple[int, int]:
    try:
        import openslide

        with openslide.OpenSlide(str(slide_path)) as slide:
            width, height = slide.dimensions
            return int(width), int(height)
    except Exception:
        with tifffile.TiffFile(slide_path) as tif:
            page = tif.pages[0]
            return int(page.imagewidth), int(page.imagelength)


def _load_best_mask_level(
    mask_path: Path,
    slide_width: int,
    slide_height: int,
    downsample: int,
) -> tuple[Any, float, float]:
    target_width = max(slide_width / max(downsample, 1), 1.0)
    target_height = max(slide_height / max(downsample, 1), 1.0)
    with tifffile.TiffFile(mask_path) as tif:
        best_index = 0
        best_score: float | None = None
        for index, page in enumerate(tif.pages):
            score = abs(page.imagewidth - target_width) + abs(page.imagelength - target_height)
            if best_score is None or score < best_score:
                best_index = index
                best_score = score
        mask = tif.pages[best_index].asarray()
    if getattr(mask, "ndim", 0) > 2:
        mask = mask[..., 0]
    mask_height = int(mask.shape[0])
    mask_width = int(mask.shape[1])
    scale_x = mask_width / target_width
    scale_y = mask_height / target_height
    return mask, scale_x, scale_y


def _compute_gold_camelyon_tiles(
    answer_row: dict[str, Any],
    slide_path: Path,
    hidden_cache_root: Path,
) -> list[dict[str, int]]:
    source_name = str(answer_row.get("source_slide_name", "camelyon_slide"))
    if "mask_path" in answer_row:
        mask_path = Path(str(answer_row["mask_path"])).expanduser().resolve()
    else:
        mask_url = str(answer_row["mask_url"])
        mask_path = _download_hidden_file(
            mask_url,
            hidden_cache_root / "camelyon_masks" / f"{source_name}_mask.tif",
        )
    tile_size = int(answer_row["tile_size"])
    downsample = int(answer_row["analysis_downsample"])
    threshold = float(answer_row["tumor_threshold"])

    slide_width, slide_height = _open_slide_dimensions(slide_path)
    mask, scale_x, scale_y = _load_best_mask_level(
        mask_path, slide_width, slide_height, downsample
    )
    mask_height, mask_width = int(mask.shape[0]), int(mask.shape[1])
    target_width = max(slide_width / max(downsample, 1), 1.0)
    target_height = max(slide_height / max(downsample, 1), 1.0)

    grid_width = int((target_width + tile_size - 1) // tile_size)
    grid_height = int((target_height + tile_size - 1) // tile_size)

    positives: list[dict[str, int]] = []
    for grid_y in range(grid_height):
        for grid_x in range(grid_width):
            x0 = int(round(grid_x * tile_size * scale_x))
            x1 = int(round((grid_x + 1) * tile_size * scale_x))
            y0 = int(round(grid_y * tile_size * scale_y))
            y1 = int(round((grid_y + 1) * tile_size * scale_y))
            x1 = min(max(x1, x0 + 1), mask_width)
            y1 = min(max(y1, y0 + 1), mask_height)
            patch = mask[y0:y1, x0:x1]
            if patch.size == 0:
                continue
            tumor_fraction = float((patch == 2).sum()) / float(patch.size)
            if tumor_fraction >= threshold:
                positives.append({"x": grid_x, "y": grid_y})
    return positives


def _compute_camelyon_tumor_coverage(
    predicted_tiles: set[tuple[int, int]],
    answer_row: dict[str, Any],
    slide_path: Path,
    hidden_cache_root: Path,
) -> dict[str, float]:
    source_name = str(answer_row.get("source_slide_name", "camelyon_slide"))
    if "mask_path" in answer_row:
        mask_path = Path(str(answer_row["mask_path"])).expanduser().resolve()
    elif "mask_url" not in answer_row:
        return {
            "tumor_coverage": 0.0,
            "tumor_pixels_total": 0.0,
            "tumor_pixels_covered": 0.0,
        }
    else:
        mask_url = str(answer_row["mask_url"])
        mask_path = _download_hidden_file(
            mask_url,
            hidden_cache_root / "camelyon_masks" / f"{source_name}_mask.tif",
        )
    tile_size = int(answer_row["tile_size"])
    downsample = int(answer_row["analysis_downsample"])

    slide_width, slide_height = _open_slide_dimensions(slide_path)
    mask, scale_x, scale_y = _load_best_mask_level(
        mask_path, slide_width, slide_height, downsample
    )
    mask_height, mask_width = int(mask.shape[0]), int(mask.shape[1])
    total_tumor_pixels = int((mask == 2).sum())
    if total_tumor_pixels <= 0:
        return {
            "tumor_coverage": 0.0,
            "tumor_pixels_total": 0.0,
            "tumor_pixels_covered": 0.0,
        }

    covered_tumor_pixels = 0
    for grid_x, grid_y in sorted(predicted_tiles):
        x0 = int(round(grid_x * tile_size * scale_x))
        x1 = int(round((grid_x + 1) * tile_size * scale_x))
        y0 = int(round(grid_y * tile_size * scale_y))
        y1 = int(round((grid_y + 1) * tile_size * scale_y))
        x1 = min(max(x1, x0 + 1), mask_width)
        y1 = min(max(y1, y0 + 1), mask_height)
        if x0 >= mask_width or y0 >= mask_height or x1 <= x0 or y1 <= y0:
            continue
        patch = mask[y0:y1, x0:x1]
        if patch.size == 0:
            continue
        covered_tumor_pixels += int((patch == 2).sum())

    return {
        "tumor_coverage": covered_tumor_pixels / total_tumor_pixels,
        "tumor_pixels_total": float(total_tumor_pixels),
        "tumor_pixels_covered": float(covered_tumor_pixels),
    }


def _hydrate_answer_key(
    rows: list[dict[str, Any]],
    slide_path: Path,
    hidden_cache_root: Path,
) -> list[dict[str, Any]]:
    hydrated: list[dict[str, Any]] = []
    for row in rows:
        shaped = dict(row)
        if shaped.get("subset") == "camelyon16" and "expected_tumor_tiles" not in shaped:
            shaped["expected_tumor_tiles"] = _compute_gold_camelyon_tiles(
                shaped, slide_path, hidden_cache_root
            )
        hydrated.append(shaped)
    return hydrated


def _attach_camelyon_coverage_metrics(
    summary: dict[str, Any],
    submission_rows: list[dict[str, Any]],
    answer_rows: list[dict[str, Any]],
    slide_path: Path,
    hidden_cache_root: Path,
) -> None:
    submissions_by_id = {
        str(row.get("task_id", "")): row for row in submission_rows if isinstance(row, dict)
    }
    answers_by_id = {
        str(row.get("task_id", "")): row for row in answer_rows if isinstance(row, dict)
    }
    for result_row in summary.get("results", []):
        if not isinstance(result_row, dict):
            continue
        if str(result_row.get("subset", "")) != "camelyon16":
            continue
        task_id = str(result_row.get("task_id", ""))
        submission_row = submissions_by_id.get(task_id, {})
        answer_row = answers_by_id.get(task_id, {})
        coverage = _compute_camelyon_tumor_coverage(
            _normalize_tile_set(submission_row.get("predicted_tumor_tiles")),
            answer_row,
            slide_path,
            hidden_cache_root,
        )
        result_row.update(coverage)


def main() -> int:
    args = _parse_args()
    args.reward_file.parent.mkdir(parents=True, exist_ok=True)
    args.reward_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.error_analysis_file.parent.mkdir(parents=True, exist_ok=True)
    if args.reward_file.exists():
        args.reward_file.unlink()

    if not args.submission.exists():
        args.reward_json.write_text(json.dumps({"reward": 0.0}) + "\n", encoding="utf-8")
        args.results_json.write_text(
            json.dumps({"status": "error", "error": "missing submission"}, indent=2) + "\n",
            encoding="utf-8",
        )
        return 1

    submission_rows = load_submission_text(args.submission.read_text(encoding="utf-8"))
    answer_key_rows = _load_json(args.answer_key)
    if not isinstance(answer_key_rows, list):
        raise ValueError("answer key must be a JSON list")

    slide_path = _materialized_slide_file(args.slide_path)
    hydrated_answer_key = _hydrate_answer_key(
        [dict(row) for row in answer_key_rows if isinstance(row, dict)],
        slide_path,
        args.hidden_cache_root,
    )
    summary = evaluate_submission_rows(submission_rows, hydrated_answer_key)
    _attach_camelyon_coverage_metrics(
        summary,
        submission_rows,
        hydrated_answer_key,
        slide_path,
        args.hidden_cache_root,
    )

    if summary["results"]:
        first = summary["results"][0]
        subset = str(first.get("subset", "unknown"))
        reward = float(first.get("reward", 0.0))
        reward_payload = {"reward": reward}
        if subset == "tcga":
            reward_payload.update(
                {
                    "tcga_tp": int(first.get("tp", 0)),
                    "tcga_fp": int(first.get("fp", 0)),
                    "tcga_fn": int(first.get("fn", 0)),
                    "tcga_tn": int(first.get("tn", 0)),
                    "cam_tp": 0,
                    "cam_fp": 0,
                    "cam_fn": 0,
                }
            )
        else:
            reward_payload.update(
                {
                    "tcga_tp": 0,
                    "tcga_fp": 0,
                    "tcga_fn": 0,
                    "tcga_tn": 0,
                    "cam_tp": int(first.get("tp", 0)),
                    "cam_fp": int(first.get("fp", 0)),
                    "cam_fn": int(first.get("fn", 0)),
                    "cam_tumor_coverage": float(first.get("tumor_coverage", 0.0)),
                }
            )
    else:
        subset = "unknown"
        reward_payload = {
            "reward": 0.0,
            "tcga_tp": 0,
            "tcga_fp": 0,
            "tcga_fn": 0,
            "tcga_tn": 0,
            "cam_tp": 0,
            "cam_fp": 0,
            "cam_fn": 0,
            "cam_tumor_coverage": 0.0,
        }

    # Harbor prefers reward.txt when both are present, but this benchmark needs
    # the structured subset counts from reward.json for exact aggregation.
    args.reward_json.write_text(json.dumps(reward_payload) + "\n", encoding="utf-8")
    args.results_json.write_text(
        json.dumps(
            {
                "status": "success",
                "subset": subset,
                "reward": reward_payload["reward"],
                "summary": summary,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    args.error_analysis_file.write_text(
        json.dumps(summary["results"], indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
