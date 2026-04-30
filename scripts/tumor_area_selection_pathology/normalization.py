"""Shared normalization helpers for tumor_area_selection_pathology."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BENCHMARK_NAME = "tumor_area_selection_pathology"
TCGA_SUBSET = "tcga"
CAMELYON_SUBSET = "camelyon16"
TCGA_TASK_PREFIX = "tcga_slide"
CAMELYON_TASK_PREFIX = "camelyon_slide"
TUMOR_SLIDE_SELECTION_NAME = "tumor slide selection"
TUMOR_AREA_SELECTION_NAME = "tumor area selection"

DEFAULT_TILE_SIZE = 256
DEFAULT_ANALYSIS_DOWNSAMPLE = 16
CAMELYON_TUMOR_THRESHOLD = 0.20


def load_manifest(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Manifest must be a JSON list: {path}")
    return [dict(row) for row in payload if isinstance(row, dict)]


def task_subset(row: dict[str, Any]) -> str:
    subset = str(row.get("subset", "")).strip().lower()
    if subset not in {TCGA_SUBSET, CAMELYON_SUBSET}:
        raise ValueError(f"Unknown subset: {subset}")
    return subset


def build_task_name(row: dict[str, Any]) -> str:
    return str(row["task_name"])


def subset_display_name(subset: str) -> str:
    if subset == TCGA_SUBSET:
        return TUMOR_SLIDE_SELECTION_NAME
    if subset == CAMELYON_SUBSET:
        return TUMOR_AREA_SELECTION_NAME
    raise ValueError(f"Unknown subset: {subset}")


def build_public_instruction(row: dict[str, Any]) -> str:
    subset = task_subset(row)
    if subset == TCGA_SUBSET:
        return (
            "Complete the tumor slide selection task for the current whole-slide image. "
            "Determine whether the slide contains tumor. "
            "Use the pathology helper scripts to inspect the slide. "
            "Set `contains_tumor` to true or false and leave "
            "`predicted_tumor_tiles` empty."
        )
    return (
        "Complete the tumor area selection task for the current whole-slide image. "
        "Determine whether tumor is present. "
        "If tumor is present, identify every tile on the benchmark analysis grid "
        "that you believe contains tumor and write those tile coordinates into "
        "`predicted_tumor_tiles`. Use the pathology helper scripts to navigate "
        "the slide and inspect local regions."
    )


def build_public_task_row(row: dict[str, Any]) -> dict[str, Any]:
    subset = task_subset(row)
    task_id = str(row["task_id"])
    payload = {
        "task_id": task_id,
        "subset": subset,
        "task_type": subset_display_name(subset),
        "instruction": build_public_instruction(row),
        "analysis_tile_size": int(row.get("tile_size", DEFAULT_TILE_SIZE)),
        "analysis_downsample": int(
            row.get("analysis_downsample", DEFAULT_ANALYSIS_DOWNSAMPLE)
        ),
    }
    if subset == CAMELYON_SUBSET:
        payload["tumor_threshold"] = float(
            row.get("tumor_threshold", CAMELYON_TUMOR_THRESHOLD)
        )
    return payload


def build_submission_row(row: dict[str, Any]) -> dict[str, Any]:
    public_row = build_public_task_row(row)
    return {
        "task_id": public_row["task_id"],
        "instruction": public_row["instruction"],
        "contains_tumor": False,
        "predicted_tumor_tiles": [],
    }


def build_answer_key_row(row: dict[str, Any]) -> dict[str, Any]:
    subset = task_subset(row)
    answer = {
        "task_id": str(row["task_id"]),
        "subset": subset,
        "expected_contains_tumor": bool(row["contains_tumor"]),
        "tile_size": int(row.get("tile_size", DEFAULT_TILE_SIZE)),
        "analysis_downsample": int(
            row.get("analysis_downsample", DEFAULT_ANALYSIS_DOWNSAMPLE)
        ),
    }
    if subset == TCGA_SUBSET:
        answer.update(
            {
                "source_file_id": str(row["source_file_id"]),
                "source_label_name": str(row["source_label_name"]),
            }
        )
    else:
        answer.update(
            {
                "mask_url": str(row["mask_url"]),
                "annotation_url": str(row["annotation_url"]),
                "tumor_threshold": float(
                    row.get("tumor_threshold", CAMELYON_TUMOR_THRESHOLD)
                ),
                "source_slide_name": str(row["source_slide_name"]),
            }
        )
    return answer


def build_runtime_manifest(row: dict[str, Any]) -> dict[str, Any]:
    subset = task_subset(row)
    base = {
        "task_id": str(row["task_id"]),
        "subset": subset,
        "tile_size": int(row.get("tile_size", DEFAULT_TILE_SIZE)),
        "analysis_downsample": int(
            row.get("analysis_downsample", DEFAULT_ANALYSIS_DOWNSAMPLE)
        ),
        "cache_key": str(row["task_name"]),
    }
    if subset == TCGA_SUBSET:
        base.update(
            {
                "download_url": str(row["download_url"]),
                "source_file_id": str(row["source_file_id"]),
                "slide_extension": ".svs",
            }
        )
    else:
        base.update(
            {
                "download_url": str(row["image_url"]),
                "slide_extension": ".tif",
                "source_slide_name": str(row["source_slide_name"]),
            }
        )
    return base
