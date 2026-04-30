"""Common runtime helpers for pathology Harbor tasks."""

from __future__ import annotations

import json
import math
import os
import shutil
import urllib.request
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import tifffile
from PIL import Image


WORKSPACE = Path("/workspace")
SLIDE_DIR = Path("/data/slide/current")
TOOL_OUTPUT_DIR = WORKSPACE / "tool_outputs"
TASK_MANIFEST_PATH = Path("/opt/task_manifest.json")
TCGA_CACHE_DIR = Path("/data/cache/tcga")
CAMELYON_CACHE_DIR = Path("/data/cache/camelyon16/slides")
DEFAULT_MASK_THUMBNAIL_SIZE = 1024
DEFAULT_REGION_MAX_OUTPUT_SIZE = 2048


@lru_cache(maxsize=1)
def _open_benchmark_payload() -> list[dict[str, Any]]:
    payload = json.loads((WORKSPACE / "benchmark_tasks.json").read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("benchmark_tasks.json must be a list")
    return [dict(row) for row in payload if isinstance(row, dict)]


@lru_cache(maxsize=1)
def current_task() -> dict[str, Any]:
    payload = _open_benchmark_payload()
    if not payload:
        raise ValueError("benchmark_tasks.json is empty")
    return payload[0]


@lru_cache(maxsize=1)
def task_manifest() -> dict[str, Any]:
    if not TASK_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing task manifest at {TASK_MANIFEST_PATH}")
    return json.loads(TASK_MANIFEST_PATH.read_text(encoding="utf-8"))


def _cached_slide_path(manifest: dict[str, Any]) -> Path:
    subset = str(manifest["subset"])
    extension = str(manifest["slide_extension"])
    if subset == "tcga":
        cache_name = f"{manifest['source_file_id']}{extension}"
        return TCGA_CACHE_DIR / cache_name
    cache_name = f"{manifest['source_slide_name']}{extension}"
    return CAMELYON_CACHE_DIR / cache_name


def _download_slide_if_needed(manifest: dict[str, Any], cached_path: Path) -> None:
    cached_path.parent.mkdir(parents=True, exist_ok=True)
    download_url = str(manifest["download_url"])
    if cached_path.exists() and cached_path.stat().st_size > 0:
        return
    tmp_path = cached_path.with_suffix(cached_path.suffix + ".part")
    with urllib.request.urlopen(download_url, timeout=600) as response, tmp_path.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    tmp_path.replace(cached_path)


def _materialize_runtime_slide() -> None:
    slide_exists = any(candidate.is_file() for candidate in sorted(SLIDE_DIR.glob("slide.*")))
    manifest_exists = (SLIDE_DIR / "manifest.json").is_file()
    if slide_exists and manifest_exists:
        return

    manifest = task_manifest()
    cached_path = _cached_slide_path(manifest)
    _download_slide_if_needed(manifest, cached_path)

    extension = str(manifest["slide_extension"])
    public_manifest = {
        "task_id": manifest["task_id"],
        "subset": manifest["subset"],
        "tile_size": manifest["tile_size"],
        "analysis_downsample": manifest["analysis_downsample"],
        "slide_path": f"/data/slide/current/slide{extension}",
    }

    SLIDE_DIR.mkdir(parents=True, exist_ok=True)
    slide_dest = SLIDE_DIR / f"slide{extension}"
    if slide_dest.exists() or slide_dest.is_symlink():
        slide_dest.unlink()
    os.symlink(cached_path, slide_dest)
    (SLIDE_DIR / "manifest.json").write_text(
        json.dumps(public_manifest, indent=2) + "\n",
        encoding="utf-8",
    )


@lru_cache(maxsize=1)
def runtime_manifest() -> dict[str, Any]:
    _materialize_runtime_slide()
    return json.loads((SLIDE_DIR / "manifest.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _materialized_slide_file() -> Path:
    _materialize_runtime_slide()
    for candidate in sorted(SLIDE_DIR.glob("slide.*")):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No slide.* file found under {SLIDE_DIR}")


@lru_cache(maxsize=1)
def slide_dimensions() -> tuple[int, int]:
    slide_path = _materialized_slide_file()
    try:
        import openslide

        with openslide.OpenSlide(str(slide_path)) as slide:
            width, height = slide.dimensions
            return int(width), int(height)
    except Exception:
        with tifffile.TiffFile(slide_path) as tif:
            page = tif.pages[0]
            return int(page.imagewidth), int(page.imagelength)


@lru_cache(maxsize=1)
def slide_extension() -> str:
    return _materialized_slide_file().suffix


@lru_cache(maxsize=1)
def analysis_config() -> tuple[int, int]:
    task = current_task()
    return int(task["analysis_tile_size"]), int(task["analysis_downsample"])


@lru_cache(maxsize=1)
def grid_shape() -> tuple[int, int]:
    width, height = slide_dimensions()
    tile_size, downsample = analysis_config()
    grid_width = math.ceil(width / (tile_size * downsample))
    grid_height = math.ceil(height / (tile_size * downsample))
    return grid_width, grid_height


def grid_tile_to_level0_bbox(x: int, y: int, width_tiles: int = 1, height_tiles: int = 1) -> tuple[int, int, int, int]:
    tile_size, downsample = analysis_config()
    x0 = x * tile_size * downsample
    y0 = y * tile_size * downsample
    x1 = x0 + width_tiles * tile_size * downsample
    y1 = y0 + height_tiles * tile_size * downsample
    slide_w, slide_h = slide_dimensions()
    return x0, y0, min(x1, slide_w), min(y1, slide_h)


def _resize_to_cap(
    image: Image.Image,
    max_output_size: int | None,
) -> Image.Image:
    if max_output_size is None:
        return image
    if image.width <= max_output_size and image.height <= max_output_size:
        return image
    scaled = image.copy()
    scaled.thumbnail((max_output_size, max_output_size), Image.Resampling.LANCZOS)
    return scaled


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


def _load_region_from_tiff(
    slide_path: Path,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    target_size: tuple[int, int],
    max_output_size: int | None,
) -> Image.Image:
    with tifffile.TiffFile(slide_path) as tif:
        source_width = max(x1 - x0, 1)
        source_height = max(y1 - y0, 1)
        target_width = max(target_size[0], 1)
        target_height = max(target_size[1], 1)
        desired_downsample = max(
            source_width / target_width,
            source_height / target_height,
            1.0,
        )
        page, page_downsample = _best_tiff_page(tif, desired_downsample)
        arr = page.asarray()
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    page_x0 = max(int(math.floor(x0 / page_downsample)), 0)
    page_y0 = max(int(math.floor(y0 / page_downsample)), 0)
    page_x1 = min(max(int(math.ceil(x1 / page_downsample)), page_x0 + 1), arr.shape[1])
    page_y1 = min(max(int(math.ceil(y1 / page_downsample)), page_y0 + 1), arr.shape[0])
    patch = arr[page_y0:page_y1, page_x0:page_x1]
    if patch.size == 0:
        patch = np.zeros((1, 1, 3), dtype=np.uint8)
    image = Image.fromarray(patch.astype(np.uint8)).convert("RGB")
    if image.size != (target_width, target_height):
        image = image.resize((target_width, target_height), Image.Resampling.BILINEAR)
    return _resize_to_cap(image, max_output_size)


def read_region(
    x: int,
    y: int,
    width_tiles: int = 1,
    height_tiles: int = 1,
    *,
    max_output_size: int | None = DEFAULT_REGION_MAX_OUTPUT_SIZE,
) -> Image.Image:
    x0, y0, x1, y1 = grid_tile_to_level0_bbox(x, y, width_tiles, height_tiles)
    slide_path = _materialized_slide_file()
    tile_size, _downsample = analysis_config()
    target_width = max(width_tiles * tile_size, 1)
    target_height = max(height_tiles * tile_size, 1)
    try:
        import openslide

        with openslide.OpenSlide(str(slide_path)) as slide:
            source_width = max(x1 - x0, 1)
            source_height = max(y1 - y0, 1)
            desired_downsample = max(
                source_width / target_width,
                source_height / target_height,
                1.0,
            )
            level = int(slide.get_best_level_for_downsample(desired_downsample))
            level_downsample = float(slide.level_downsamples[level])
            level_width = max(int(math.ceil(source_width / level_downsample)), 1)
            level_height = max(int(math.ceil(source_height / level_downsample)), 1)
            region = slide.read_region((x0, y0), level, (level_width, level_height)).convert("RGB")
            if region.size != (target_width, target_height):
                region = region.resize((target_width, target_height), Image.Resampling.BILINEAR)
            return _resize_to_cap(region, max_output_size)
    except Exception:
        return _load_region_from_tiff(
            slide_path,
            x0,
            y0,
            x1,
            y1,
            target_size=(target_width, target_height),
            max_output_size=max_output_size,
        )


@lru_cache(maxsize=4)
def read_thumbnail(max_size: int = 1024) -> Image.Image:
    slide_path = _materialized_slide_file()
    try:
        import openslide

        with openslide.OpenSlide(str(slide_path)) as slide:
            thumb = slide.get_thumbnail((max_size, max_size)).convert("RGB")
            return thumb
    except Exception:
        with tifffile.TiffFile(slide_path) as tif:
            page, _ = _best_tiff_page(tif, max(slide_dimensions()) / max(max_size, 1))
            arr = page.asarray()
        if arr.ndim == 2:
            arr = np.stack([arr, arr, arr], axis=-1)
        image = Image.fromarray(arr.astype(np.uint8))
        image.thumbnail((max_size, max_size))
        return image.convert("RGB")


def ensure_output_dir() -> Path:
    TOOL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return TOOL_OUTPUT_DIR


def save_image(image: Image.Image, stem: str) -> Path:
    output_dir = ensure_output_dir()
    filename = f"{stem}_{uuid.uuid4().hex[:8]}.png"
    path = output_dir / filename
    image.save(path)
    return path


def compute_tissue_mask(thumbnail: Image.Image | None = None) -> tuple[np.ndarray, Image.Image]:
    if thumbnail is None:
        thumbnail = read_thumbnail()
    arr = np.asarray(thumbnail.convert("RGB")).astype(np.float32) / 255.0
    gray = arr.mean(axis=2)
    saturation = arr.max(axis=2) - arr.min(axis=2)
    mask = (gray < 0.92) & (saturation > 0.04)
    mask_img = Image.fromarray((mask.astype(np.uint8) * 255))
    return mask.astype(np.uint8), mask_img


@lru_cache(maxsize=4)
def _cached_tissue_mask(max_size: int = DEFAULT_MASK_THUMBNAIL_SIZE) -> tuple[np.ndarray, Image.Image]:
    return compute_tissue_mask(read_thumbnail(max_size=max_size))


def tissue_fraction_for_tile(x: int, y: int) -> float:
    mask, _ = _cached_tissue_mask(DEFAULT_MASK_THUMBNAIL_SIZE)
    grid_w, grid_h = grid_shape()
    if not (0 <= x < grid_w and 0 <= y < grid_h):
        return 0.0
    mask_h, mask_w = mask.shape
    x0 = int(round(x * mask_w / grid_w))
    x1 = int(round((x + 1) * mask_w / grid_w))
    y0 = int(round(y * mask_h / grid_h))
    y1 = int(round((y + 1) * mask_h / grid_h))
    patch = mask[y0:y1, x0:x1]
    if patch.size == 0:
        return 0.0
    return float(patch.mean())


def enumerate_tissue_tiles(min_fraction: float = 0.2) -> list[dict[str, int]]:
    grid_w, grid_h = grid_shape()
    tiles: list[dict[str, int]] = []
    for y in range(grid_h):
        for x in range(grid_w):
            if tissue_fraction_for_tile(x, y) >= min_fraction:
                tiles.append({"x": x, "y": y})
    return tiles


def sample_tissue_tiles(count: int, seed: int = 42, min_fraction: float = 0.2) -> list[dict[str, int]]:
    import random

    tiles = enumerate_tissue_tiles(min_fraction=min_fraction)
    rng = random.Random(seed)
    rng.shuffle(tiles)
    return tiles[:count]


def neighbor_tiles(x: int, y: int, radius: int = 1) -> list[dict[str, int]]:
    grid_w, grid_h = grid_shape()
    rows: list[dict[str, int]] = []
    for yy in range(max(0, y - radius), min(grid_h, y + radius + 1)):
        for xx in range(max(0, x - radius), min(grid_w, x + radius + 1)):
            if xx == x and yy == y:
                continue
            rows.append({"x": xx, "y": yy})
    return rows


def weak_tumor_probability(x: int, y: int) -> dict[str, Any]:
    image = read_region(x, y, 1, 1).convert("RGB").resize((256, 256))
    arr = np.asarray(image).astype(np.float32) / 255.0
    tissue = tissue_fraction_for_tile(x, y)
    if tissue <= 0.01:
        return {"probability": 0.0, "backend": "heuristic", "tissue_fraction": tissue}
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    purple = np.clip(((r + b) / 2.0) - g, 0.0, 1.0).mean()
    texture = arr.std(axis=(0, 1)).mean()
    darkness = float(1.0 - arr.mean())
    raw = -1.25 + (2.8 * purple) + (1.8 * texture) + (0.8 * darkness) + (0.9 * tissue)
    probability = 1.0 / (1.0 + math.exp(-raw))
    return {
        "probability": round(float(probability), 6),
        "backend": "heuristic",
        "tissue_fraction": round(float(tissue), 6),
        "purple_score": round(float(purple), 6),
        "texture_score": round(float(texture), 6),
    }


def _gigapath_cache_path() -> Path:
    task_id = str(runtime_manifest()["task_id"])
    configured = os.environ.get("MEDCLI_TUMOR_PATH_GIGAPATH_CACHE", "").strip()
    cache_root = Path(configured).expanduser() if configured else Path("/data/cache/gigapath")
    try:
        cache_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        cache_root = WORKSPACE / ".cache" / "gigapath"
        cache_root.mkdir(parents=True, exist_ok=True)
    return cache_root / f"{task_id}.json"


@lru_cache(maxsize=1)
def _load_gigapath_model_bundle() -> tuple[str, Any, Any]:
    import torch
    import timm
    from torchvision import transforms

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = timm.create_model("hf_hub:prov-gigapath/prov-gigapath", pretrained=True)
    model.to(device)
    model.eval()

    transform = transforms.Compose(
        [
            transforms.Resize(256, interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=(0.485, 0.456, 0.406),
                std=(0.229, 0.224, 0.225),
            ),
        ]
    )
    return device, model, transform


def load_gigapath_cache() -> dict[str, Any] | None:
    path = _gigapath_cache_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _heuristic_attention_cache(max_tiles: int = 256, reason: str | None = None) -> dict[str, Any]:
    candidate_tiles = enumerate_tissue_tiles(min_fraction=0.2)[:max_tiles]
    scores: list[dict[str, Any]] = []
    for tile in candidate_tiles:
        payload = weak_tumor_probability(int(tile["x"]), int(tile["y"]))
        scores.append(
            {
                "x": int(tile["x"]),
                "y": int(tile["y"]),
                "score": round(float(payload.get("probability", 0.0)), 6),
            }
        )
    scores.sort(key=lambda row: (-float(row["score"]), int(row["y"]), int(row["x"])))
    payload: dict[str, Any] = {
        "backend": "heuristic_fallback",
        "scores": scores,
        "max_tiles": max_tiles,
    }
    if reason:
        payload["fallback_reason"] = reason
    _gigapath_cache_path().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _compute_gigapath_cache(max_tiles: int = 256) -> dict[str, Any]:
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not hf_token:
        return _heuristic_attention_cache(max_tiles=max_tiles, reason="missing_hf_token")

    try:
        import torch

        device, model, transform = _load_gigapath_model_bundle()

        candidate_tiles = enumerate_tissue_tiles(min_fraction=0.2)[:max_tiles]
        if not candidate_tiles:
            return {
                "backend": "gigapath",
                "scores": [],
                "max_tiles": max_tiles,
            }

        embeddings: list[np.ndarray] = []
        score_rows: list[dict[str, Any]] = []
        with torch.no_grad():
            for tile in candidate_tiles:
                tile_img = read_region(int(tile["x"]), int(tile["y"]), 1, 1).convert("RGB")
                tensor = transform(tile_img).unsqueeze(0).to(device)
                embedding = model(tensor).squeeze().detach().cpu().numpy()
                embeddings.append(embedding)
        stacked = np.stack(embeddings, axis=0)
        center = stacked.mean(axis=0, keepdims=True)
        scores = np.linalg.norm(stacked - center, axis=1)
        if scores.max() > scores.min():
            scores = (scores - scores.min()) / (scores.max() - scores.min())
        else:
            scores = np.zeros_like(scores)

        for tile, score in zip(candidate_tiles, scores, strict=True):
            score_rows.append(
                {
                    "x": int(tile["x"]),
                    "y": int(tile["y"]),
                    "score": round(float(score), 6),
                }
            )
        payload = {"backend": "gigapath", "scores": score_rows, "max_tiles": max_tiles}
        _gigapath_cache_path().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload
    except Exception as exc:
        return _heuristic_attention_cache(
            max_tiles=max_tiles,
            reason=f"gigapath_runtime_error:{type(exc).__name__}",
        )


def get_gigapath_scores(max_tiles: int = 256) -> dict[str, Any]:
    cached = load_gigapath_cache()
    if cached is not None:
        return cached
    return _compute_gigapath_cache(max_tiles=max_tiles)


def gigapath_heatmap_image(max_size: int = 1024, max_tiles: int = 256) -> tuple[dict[str, Any], Path]:
    payload = get_gigapath_scores(max_tiles=max_tiles)
    thumb = read_thumbnail(max_size=max_size)
    draw = np.asarray(thumb).astype(np.float32)
    grid_w, grid_h = grid_shape()
    heat = np.zeros((grid_h, grid_w), dtype=np.float32)
    for row in payload.get("scores", []):
        if not isinstance(row, dict):
            continue
        x = int(row["x"])
        y = int(row["y"])
        if 0 <= x < grid_w and 0 <= y < grid_h:
            heat[y, x] = float(row["score"])
    if heat.max() > 0:
        heat = heat / heat.max()
    thumb_h, thumb_w = draw.shape[:2]
    for y in range(grid_h):
        for x in range(grid_w):
            x0 = int(round(x * thumb_w / grid_w))
            x1 = int(round((x + 1) * thumb_w / grid_w))
            y0 = int(round(y * thumb_h / grid_h))
            y1 = int(round((y + 1) * thumb_h / grid_h))
            if x1 <= x0 or y1 <= y0:
                continue
            score = heat[y, x]
            draw[y0:y1, x0:x1, 0] = np.clip(draw[y0:y1, x0:x1, 0] * (1.0 + score), 0, 255)
    image = Image.fromarray(draw.astype(np.uint8))
    return payload, save_image(image, "gigapath_heatmap")


def topk_attention_tiles(k: int = 10, max_tiles: int = 256) -> dict[str, Any]:
    payload = get_gigapath_scores(max_tiles=max_tiles)
    scores = [row for row in payload.get("scores", []) if isinstance(row, dict)]
    scores.sort(key=lambda row: (-float(row.get("score", 0.0)), int(row.get("y", 0)), int(row.get("x", 0))))
    return {
        "backend": payload.get("backend", "gigapath"),
        "tiles": [
            {"x": int(row["x"]), "y": int(row["y"]), "score": float(row["score"])}
            for row in scores[:k]
        ],
    }
