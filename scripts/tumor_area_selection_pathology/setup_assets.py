#!/usr/bin/env python3
"""Bootstrap deterministic manifests and optional shared caches."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any

import requests

from normalization import (
    BENCHMARK_NAME,
    CAMELYON_SUBSET,
    CAMELYON_TASK_PREFIX,
    CAMELYON_TUMOR_THRESHOLD,
    DEFAULT_ANALYSIS_DOWNSAMPLE,
    DEFAULT_TILE_SIZE,
    TCGA_SUBSET,
    TCGA_TASK_PREFIX,
)


GDC_FILES_URL = "https://api.gdc.cancer.gov/files"
GDC_DATA_URL = "https://api.gdc.cancer.gov/data"
CAMELYON_BUCKET = "https://camelyon-dataset.s3.amazonaws.com/CAMELYON16"
TCGA_TUMOR_COUNTS = {"Primary Tumor": 50, "Metastatic": 50}
TCGA_NORMAL_COUNT = 100
RNG_SEED = 42

CAMELYON_NON_EXHAUSTIVE = {
    "tumor_010",
    "tumor_015",
    "tumor_018",
    "tumor_020",
    "tumor_025",
    "tumor_029",
    "tumor_033",
    "tumor_034",
    "tumor_044",
    "tumor_046",
    "tumor_051",
    "tumor_054",
    "tumor_055",
    "tumor_056",
    "tumor_067",
    "tumor_079",
    "tumor_085",
    "tumor_092",
    "tumor_095",
    "tumor_110",
}

CAMELYON_SELECTED_SLIDES = [
    "tumor_076",
    "tumor_089",
    "tumor_078",
    "tumor_026",
    "tumor_009",
    "tumor_047",
    "tumor_102",
    "tumor_058",
    "tumor_082",
    "tumor_068",
]
DEFAULT_EXTERNAL_CACHE_ROOT = Path(
    os.environ.get(
        "MEDCLI_TUMOR_PATH_CACHE_ROOT",
        str(Path.home() / "harbor-cache" / BENCHMARK_NAME),
    )
).expanduser()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=Path("scripts") / BENCHMARK_NAME / "assets",
    )
    parser.add_argument(
        "--download-slides",
        action="store_true",
        help="Warm the shared slide caches after writing manifests.",
    )
    parser.add_argument(
        "--download-camelyon-masks",
        action="store_true",
        help="Also warm the hidden CAMELYON mask cache.",
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=DEFAULT_EXTERNAL_CACHE_ROOT,
        help="External shared cache root outside the git repo.",
    )
    return parser.parse_args()


def _gdc_query(sample_type: str) -> list[dict[str, Any]]:
    filters = {
        "op": "and",
        "content": [
            {"op": "=", "content": {"field": "files.data_type", "value": ["Slide Image"]}},
            {
                "op": "=",
                "content": {
                    "field": "files.experimental_strategy",
                    "value": ["Tissue Slide"],
                },
            },
            {
                "op": "=",
                "content": {
                    "field": "cases.samples.sample_type",
                    "value": [sample_type],
                },
            },
            {"op": "=", "content": {"field": "files.access", "value": ["open"]}},
            {
                "op": "in",
                "content": {"field": "files.data_format", "value": ["SVS", "TIF", "TIFF"]},
            },
        ],
    }
    params = {
        "filters": json.dumps(filters),
        "fields": ",".join(
            [
                "file_id",
                "file_name",
                "data_format",
                "cases.project.project_id",
                "cases.submitter_id",
                "cases.samples.sample_type",
            ]
        ),
        "size": 5000,
        "format": "JSON",
    }
    response = requests.get(GDC_FILES_URL, params=params, timeout=120)
    response.raise_for_status()
    hits = response.json()["data"]["hits"]
    rows: list[dict[str, Any]] = []
    for hit in hits:
        cases = hit.get("cases") or []
        if not cases:
            continue
        case = cases[0]
        project_id = str(((case.get("project") or {}).get("project_id") or "")).strip()
        if not project_id.startswith("TCGA-"):
            continue
        submitter_id = str(case.get("submitter_id", "")).strip()
        if not submitter_id:
            continue
        rows.append(
            {
                "source_file_id": str(hit["file_id"]),
                "original_file_name": str(hit.get("file_name", "")),
                "project_id": project_id,
                "submitter_id": submitter_id,
                "source_label_name": sample_type,
                "contains_tumor": sample_type != "Solid Tissue Normal",
                "subset": TCGA_SUBSET,
                "download_url": f"{GDC_DATA_URL}/{hit['file_id']}",
                "tile_size": DEFAULT_TILE_SIZE,
                "analysis_downsample": DEFAULT_ANALYSIS_DOWNSAMPLE,
            }
        )
    rows.sort(key=lambda row: (row["project_id"], row["submitter_id"], row["source_file_id"]))
    # Keep one slide per submitter_id for diversity.
    deduped: list[dict[str, Any]] = []
    seen_submitters: set[str] = set()
    for row in rows:
        if row["submitter_id"] in seen_submitters:
            continue
        seen_submitters.add(row["submitter_id"])
        deduped.append(row)
    return deduped


def _sample_tcga_manifest() -> list[dict[str, Any]]:
    rng = random.Random(RNG_SEED)
    primary = _gdc_query("Primary Tumor")
    metastatic = _gdc_query("Metastatic")
    normal = _gdc_query("Solid Tissue Normal")

    if len(primary) < TCGA_TUMOR_COUNTS["Primary Tumor"]:
        raise ValueError("Not enough Primary Tumor slides to build TCGA subset")
    if len(metastatic) < TCGA_TUMOR_COUNTS["Metastatic"]:
        raise ValueError("Not enough Metastatic slides to build TCGA subset")
    if len(normal) < TCGA_NORMAL_COUNT:
        raise ValueError("Not enough Solid Tissue Normal slides to build TCGA subset")

    def pick(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
        indices = list(range(len(rows)))
        rng.shuffle(indices)
        selected = [rows[i] for i in sorted(indices[:n])]
        return [dict(row) for row in selected]

    chosen = (
        pick(primary, TCGA_TUMOR_COUNTS["Primary Tumor"])
        + pick(metastatic, TCGA_TUMOR_COUNTS["Metastatic"])
        + pick(normal, TCGA_NORMAL_COUNT)
    )
    chosen.sort(key=lambda row: (row["contains_tumor"], row["project_id"], row["submitter_id"]))

    manifest: list[dict[str, Any]] = []
    for index, row in enumerate(chosen, start=1):
        task_name = f"{TCGA_TASK_PREFIX}_{index:04d}"
        payload = dict(row)
        payload["task_name"] = task_name
        payload["task_id"] = task_name
        manifest.append(payload)
    return manifest


def _build_camelyon_manifest() -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for index, slide_name in enumerate(CAMELYON_SELECTED_SLIDES, start=1):
        if slide_name in CAMELYON_NON_EXHAUSTIVE:
            raise ValueError(f"Configured CAMELYON slide is not exhaustively annotated: {slide_name}")
        task_name = f"{CAMELYON_TASK_PREFIX}_{index:04d}"
        manifest.append(
            {
                "task_name": task_name,
                "task_id": task_name,
                "subset": CAMELYON_SUBSET,
                "source_slide_name": slide_name,
                "contains_tumor": True,
                "image_url": f"{CAMELYON_BUCKET}/images/{slide_name}.tif",
                "mask_url": f"{CAMELYON_BUCKET}/masks/{slide_name}_mask.tif",
                "annotation_url": f"{CAMELYON_BUCKET}/annotations/{slide_name}.xml",
                "tile_size": DEFAULT_TILE_SIZE,
                "analysis_downsample": DEFAULT_ANALYSIS_DOWNSAMPLE,
                "tumor_threshold": CAMELYON_TUMOR_THRESHOLD,
            }
        )
    return manifest


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)


def _warm_tcga_cache(cache_root: Path, manifest: list[dict[str, Any]]) -> None:
    for row in manifest:
        file_id = str(row["source_file_id"])
        destination = cache_root / f"{file_id}.svs"
        _download_file(str(row["download_url"]), destination)


def _warm_camelyon_cache(
    cache_root: Path,
    mask_cache_root: Path,
    manifest: list[dict[str, Any]],
    *,
    include_masks: bool,
) -> None:
    for row in manifest:
        slide_name = str(row["source_slide_name"])
        slide_path = cache_root / f"{slide_name}.tif"
        _download_file(str(row["image_url"]), slide_path)
        if include_masks:
            mask_path = mask_cache_root / f"{slide_name}_mask.tif"
            _download_file(str(row["mask_url"]), mask_path)


def main() -> None:
    args = _parse_args()
    assets_dir = args.assets_dir
    cache_root = args.cache_root.expanduser().resolve()
    tcga_manifest = _sample_tcga_manifest()
    camelyon_manifest = _build_camelyon_manifest()

    _write_json(assets_dir / "tcga_slide_manifest.json", tcga_manifest)
    _write_json(assets_dir / "camelyon16_slide_manifest.json", camelyon_manifest)

    tcga_cache = cache_root / "tcga"
    camelyon_cache = cache_root / "camelyon16" / "slides"
    camelyon_mask_cache = cache_root / "camelyon16" / "masks"
    gigapath_cache = cache_root / "gigapath"

    for path in (tcga_cache, camelyon_cache, camelyon_mask_cache, gigapath_cache):
        path.mkdir(parents=True, exist_ok=True)

    if args.download_slides:
        _warm_tcga_cache(tcga_cache, tcga_manifest)
        _warm_camelyon_cache(
            camelyon_cache,
            camelyon_mask_cache,
            camelyon_manifest,
            include_masks=args.download_camelyon_masks,
        )

    print(
        json.dumps(
            {
                "tcga_tasks": len(tcga_manifest),
                "camelyon_tasks": len(camelyon_manifest),
                "cache_root": str(cache_root),
                "tcga_cache": str(tcga_cache),
                "camelyon_cache": str(camelyon_cache),
                "camelyon_mask_cache": str(camelyon_mask_cache),
                "gigapath_cache": str(gigapath_cache),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
