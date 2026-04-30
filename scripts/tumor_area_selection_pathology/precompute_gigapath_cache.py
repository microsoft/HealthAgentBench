#!/usr/bin/env python3
"""Precompute GigaPath cache JSON files for tumor_area_selection_pathology tasks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
from pathlib import Path
from typing import Any

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
BENCHMARK_NAME = "tumor_area_selection_pathology"
DEFAULT_TASK_ROOT = Path.home() / "code" / "MedCLI" / "tasks" / BENCHMARK_NAME
DEFAULT_CACHE_ROOT = Path.home() / "harbor-cache" / BENCHMARK_NAME
DEFAULT_HF_HOME = Path.home() / ".cache" / "huggingface"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, default=DEFAULT_TASK_ROOT)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--hf-home", type=Path, default=DEFAULT_HF_HOME)
    parser.add_argument("--max-tiles", type=int, default=256)
    parser.add_argument("--selected-task-ids", help="Optional comma-separated task ids to precompute.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def _load_runtime_module():
    spec = importlib.util.spec_from_file_location(
        "tumor_pathology_common_precompute",
        SCRIPT_DIR / "runtime" / "lib" / "pathology_common.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load pathology_common.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selected_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def _slide_path(task_manifest: dict[str, Any], cache_root: Path) -> Path:
    subset = str(task_manifest["subset"])
    extension = str(task_manifest.get("slide_extension", ".tif"))
    if subset == "tcga":
        return cache_root / "tcga" / f"{task_manifest['source_file_id']}{extension}"
    return cache_root / "camelyon16" / "slides" / f"{task_manifest['source_slide_name']}{extension}"


def _download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    tmp = destination.with_suffix(destination.suffix + ".part")
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    tmp.replace(destination)
    return destination


def _clear_runtime_caches(module) -> None:
    for fn_name in (
        "_open_benchmark_payload",
        "current_task",
        "runtime_manifest",
        "_materialized_slide_file",
        "slide_dimensions",
        "slide_extension",
        "analysis_config",
        "grid_shape",
        "read_thumbnail",
        "_cached_tissue_mask",
    ):
        getattr(module, fn_name).cache_clear()


def main() -> None:
    args = _parse_args()
    selected = _selected_ids(args.selected_task_ids)
    args.cache_root.mkdir(parents=True, exist_ok=True)
    args.hf_home.mkdir(parents=True, exist_ok=True)

    os.environ["HF_HOME"] = str(args.hf_home)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(args.hf_home / "hub")
    os.environ["MEDCLI_TUMOR_PATH_GIGAPATH_CACHE"] = str(args.cache_root / "gigapath")

    if not os.environ.get("HF_TOKEN", "").strip():
        raise RuntimeError("HF_TOKEN must be set in the environment before precomputing GigaPath cache.")

    module = _load_runtime_module()
    scratch_root = args.cache_root / "gigapath_precompute_runtime"
    scratch_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    task_dirs = sorted(args.task_root.glob("*"))
    for task_dir in task_dirs:
        if not task_dir.is_dir():
            continue
        task_id = task_dir.name
        if selected and task_id not in selected:
            continue
        workspace = task_dir / "environment" / "workspace"
        task_manifest_path = task_dir / "environment" / "task_manifest.json"
        if not workspace.exists() or not task_manifest_path.exists():
            continue
        task_manifest = json.loads(task_manifest_path.read_text(encoding="utf-8"))
        cache_json = args.cache_root / "gigapath" / f"{task_id}.json"
        if cache_json.exists() and not args.force:
            try:
                payload = json.loads(cache_json.read_text(encoding="utf-8"))
                if payload.get("backend") == "gigapath":
                    rows.append({"task_id": task_id, "status": "cached", "backend": "gigapath"})
                    continue
            except Exception:
                pass

        slide_path = _slide_path(task_manifest, args.cache_root)
        if not slide_path.exists():
            slide_path = _download_file(str(task_manifest["download_url"]), slide_path)

        runtime_dir = scratch_root / task_id
        if runtime_dir.exists():
            shutil.rmtree(runtime_dir)
        runtime_dir.mkdir(parents=True, exist_ok=True)
        runtime_slide_dir = runtime_dir / "slide_current"
        runtime_slide_dir.mkdir(parents=True, exist_ok=True)

        slide_link = runtime_slide_dir / f"slide{slide_path.suffix}"
        if slide_link.exists() or slide_link.is_symlink():
            slide_link.unlink()
        slide_link.symlink_to(slide_path)
        (runtime_slide_dir / "manifest.json").write_text(
            json.dumps(task_manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        module.WORKSPACE = workspace
        module.SLIDE_DIR = runtime_slide_dir
        module.TOOL_OUTPUT_DIR = workspace / "tool_outputs"
        _clear_runtime_caches(module)

        payload = module.get_gigapath_scores(max_tiles=args.max_tiles)
        rows.append(
            {
                "task_id": task_id,
                "status": "computed",
                "backend": payload.get("backend", "unknown"),
                "num_scores": len(payload.get("scores", [])),
            }
        )
        print(json.dumps(rows[-1]), flush=True)

    summary = {
        "task_count": len(rows),
        "cache_dir": str(args.cache_root / "gigapath"),
        "hf_home": str(args.hf_home),
        "rows": rows,
    }
    summary_path = args.cache_root / "gigapath_precompute_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"task_count": len(rows), "summary_path": str(summary_path)}, indent=2))


if __name__ == "__main__":
    main()
