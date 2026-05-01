#!/usr/bin/env python3
"""Generate Harbor tasks for tumor_area_selection_pathology."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import requests
import tifffile

from normalization import (
    BENCHMARK_NAME,
    CAMELYON_SUBSET,
    CAMELYON_TUMOR_THRESHOLD,
    TCGA_SUBSET,
    build_answer_key_row,
    build_public_task_row,
    build_runtime_manifest,
    build_submission_row,
    load_manifest,
    subset_display_name,
    task_subset,
)


SCRIPT_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = SCRIPT_DIR / "runtime"
DEFAULT_EXTERNAL_CACHE_ROOT = Path.home() / "harbor-cache" / BENCHMARK_NAME
DEFAULT_TCGA_CACHE = DEFAULT_EXTERNAL_CACHE_ROOT / "tcga"
DEFAULT_CAMELYON_CACHE = DEFAULT_EXTERNAL_CACHE_ROOT / "camelyon16" / "slides"
DEFAULT_GENERATOR_HIDDEN_CACHE = DEFAULT_EXTERNAL_CACHE_ROOT / "generator_hidden"
DEFAULT_TCGA_CACHE_EXPR = "${HOME}/harbor-cache/tumor_area_selection_pathology/tcga"
DEFAULT_CAMELYON_CACHE_EXPR = (
    "${HOME}/harbor-cache/tumor_area_selection_pathology/camelyon16/slides"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--tcga-manifest",
        type=Path,
        default=SCRIPT_DIR / "assets" / "tcga_slide_manifest.json",
    )
    parser.add_argument(
        "--camelyon-manifest",
        type=Path,
        default=SCRIPT_DIR / "assets" / "camelyon16_slide_manifest.json",
    )
    parser.add_argument(
        "--selected-task-ids",
        help="Optional comma-separated task ids to generate.",
    )
    parser.add_argument(
        "--hidden-cache-root",
        type=Path,
        default=DEFAULT_GENERATOR_HIDDEN_CACHE,
        help="External cache root for generator-only hidden assets.",
    )
    return parser.parse_args()


def _split_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def _load_all_tasks(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows = load_manifest(args.tcga_manifest) + load_manifest(args.camelyon_manifest)
    selected = _split_csv(args.selected_task_ids)
    if selected:
        rows = [row for row in rows if str(row.get("task_id", "")) in selected]
        missing = selected - {str(row.get("task_id", "")) for row in rows}
        if missing:
            raise ValueError(f"Unknown selected task ids: {sorted(missing)}")
    rows.sort(key=lambda row: str(row["task_name"]))
    return rows


def _local_or_download(url: str, cache_path: Path) -> Path:
    if url.startswith("file://"):
        return Path(url[len("file://") :]).resolve()
    local_path = Path(url)
    if local_path.exists():
        return local_path.resolve()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with cache_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return cache_path


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


def _compute_gold_camelyon_tiles(row: dict[str, Any], cache_root: Path) -> list[dict[str, int]]:
    mask_path = _local_or_download(
        str(row["mask_url"]),
        cache_root / "masks" / f"{row['source_slide_name']}_mask.tif",
    )
    tile_size = int(row["tile_size"])
    downsample = int(row["analysis_downsample"])
    threshold = float(row.get("tumor_threshold", CAMELYON_TUMOR_THRESHOLD))
    with tifffile.TiffFile(mask_path) as tif:
        base_page = tif.pages[0]
        slide_w = int(base_page.imagewidth)
        slide_h = int(base_page.imagelength)

    mask, scale_x, scale_y = _load_best_mask_level(mask_path, slide_w, slide_h, downsample)
    mask_h, mask_w = int(mask.shape[0]), int(mask.shape[1])
    target_w = max(slide_w / max(downsample, 1), 1.0)
    target_h = max(slide_h / max(downsample, 1), 1.0)

    grid_w = int((target_w + tile_size - 1) // tile_size)
    grid_h = int((target_h + tile_size - 1) // tile_size)

    positives: list[dict[str, int]] = []
    for y in range(grid_h):
        for x in range(grid_w):
            x0 = int(round(x * tile_size * scale_x))
            x1 = int(round((x + 1) * tile_size * scale_x))
            y0 = int(round(y * tile_size * scale_y))
            y1 = int(round((y + 1) * tile_size * scale_y))
            x1 = min(max(x1, x0 + 1), mask_w)
            y1 = min(max(y1, y0 + 1), mask_h)
            patch = mask[y0:y1, x0:x1]
            if patch.size == 0:
                continue
            tumor_fraction = float((patch == 2).sum()) / float(patch.size)
            if tumor_fraction >= threshold:
                positives.append({"x": x, "y": y})
    return positives


def _answer_key_rows(row: dict[str, Any], cache_root: Path) -> list[dict[str, Any]]:
    answer = build_answer_key_row(row)
    if task_subset(row) == CAMELYON_SUBSET:
        answer["expected_tumor_tiles"] = _compute_gold_camelyon_tiles(row, cache_root)
    else:
        answer["expected_tumor_tiles"] = []
    return [answer]


def _task_toml(row: dict[str, Any]) -> str:
    subset = task_subset(row)
    return f"""version = "1.0"

[metadata]
benchmark = "{BENCHMARK_NAME}"
mode = "single-task"
subset = "{subset}"
task_id = "{row['task_id']}"
submission_path = "/workspace/submission.json"

[verifier]
timeout_sec = 3600.0

[agent]
timeout_sec = 7200.0

[environment]
build_timeout_sec = 3600.0
allow_internet = true
cpus = 2
memory_mb = 8192
storage_mb = 20480
gpus = 0
mcp_servers = []
"""


def _workspace_readme(row: dict[str, Any]) -> str:
    subset = task_subset(row)
    display_name = subset_display_name(subset)
    lines = [
        f"# {BENCHMARK_NAME}",
        "",
        f"Task type: `{display_name}`",
        "",
        "Files:",
        "- `benchmark_tasks.json`: public task metadata",
        "- `submission.json`: single-row structured output to fill in",
        "- `scripts/primitives/`: pathology helper scripts",
        "",
        "Useful helper examples:",
        "- `python /workspace/scripts/primitives/get_slide_thumbnail.py --max-size 1024`",
        "- `python /workspace/scripts/primitives/sample_tiles.py --count 20`",
        "- `python /workspace/scripts/primitives/get_tile.py --x 10 --y 12`",
        "- `python /workspace/scripts/primitives/classify_tile_tumor_probability.py --x 10 --y 12`",
        "",
        "Always update `submission.json` with a JSON-aware tool, not raw text editing.",
    ]
    return "\n".join(lines) + "\n"


def _instruction_md(row: dict[str, Any]) -> str:
    subset = task_subset(row)
    display_name = subset_display_name(subset)
    tile_size = int(row["tile_size"])
    downsample = int(row["analysis_downsample"])
    common = [
        f"# {display_name.title()}",
        "",
        "You are working inside a pathology task environment that contains:",
        "",
        "- the current whole-slide image at `/data/slide/current/slide.*`",
        "- a public task row in `/workspace/benchmark_tasks.json`",
        "- an editable single-row submission in `/workspace/submission.json`",
        "- pathology helper scripts under `/workspace/scripts/primitives/`",
        "",
        "Tool examples:",
        "- `python /workspace/scripts/primitives/get_slide_thumbnail.py --max-size 1024`",
        "- `python /workspace/scripts/primitives/get_tissue_mask.py`",
        "- `python /workspace/scripts/primitives/sample_tiles.py --count 20`",
        "- `python /workspace/scripts/primitives/get_tile.py --x 12 --y 44`",
        "- `python /workspace/scripts/primitives/get_region.py --x 12 --y 44 --width 3 --height 3 --max-size 1536`",
        "",
        f"The benchmark analysis grid uses {tile_size}x{tile_size} tiles at downsample {downsample}.",
        "",
    ]
    if subset == TCGA_SUBSET:
        common.extend(
            [
                "## Your Task",
                "",
                "Complete the tumor slide selection task by deciding whether this slide contains tumor.",
                "",
                "Submission requirements:",
                "- set `contains_tumor` to `true` or `false`",
                "- leave `predicted_tumor_tiles` as an empty list",
                "- do not modify `task_id` or `instruction`",
                "",
            ]
        )
    else:
        common.extend(
            [
                "## Your Task",
                "",
                "Complete the tumor area selection task by deciding whether tumor is present on this slide and predicting the set of all tumor tiles on the benchmark grid.",
                "",
                "Submission requirements:",
                "- set `contains_tumor` to `true` if you believe any tumor is present, else `false`",
                "- populate `predicted_tumor_tiles` with dictionaries of the form `{ \"x\": <int>, \"y\": <int> }`",
                "- include every tile you believe contains tumor",
                "- non-tissue tiles should be treated as non-tumor",
                "- do not modify `task_id` or `instruction`",
                "",
            ]
        )
    common.extend(
        [
            "## Important Rules",
            "",
            "- Work autonomously until the submission is complete.",
            "- Do not train models or fine-tune weights.",
            "- Use the provided helper scripts and your own reasoning over their outputs.",
            "- Update `submission.json` with a JSON-aware tool such as Python.",
        ]
    )
    return "\n".join(common) + "\n"


def _task_readme(row: dict[str, Any]) -> str:
    subset = task_subset(row)
    display_name = subset_display_name(subset)
    return (
        f"# {display_name.title()}\n\n"
        f"Task id: `{row['task_name']}`\n\n"
        "This Harbor task contains one pathology slide episode from the "
        f"`{BENCHMARK_NAME}` benchmark.\n"
    )


def _dockerfile() -> str:
    return """FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \\
    bash \\
    curl \\
    wget \\
    util-linux \\
    jq \\
    openslide-tools \\
    libopenslide0 \\
    libgl1 \\
    libglib2.0-0 \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \\
    imagecodecs \\
    numpy \\
    pillow \\
    requests \\
    tifffile \\
    openslide-python

WORKDIR /workspace

COPY environment/workspace/ /workspace/
COPY environment/task_manifest.json /opt/task_manifest.json
COPY environment/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && mkdir -p /logs/verifier /logs/artifacts /data/cache /data/slide/current

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
"""


def _docker_compose() -> str:
    return f"""services:
  main:
    build:
      context: ..
      dockerfile: environment/Dockerfile
    volumes:
      - ${{MEDCLI_TUMOR_PATH_TCGA_CACHE:-{DEFAULT_TCGA_CACHE_EXPR}}}:/data/cache/tcga:rw
      - ${{MEDCLI_TUMOR_PATH_CAMELYON_CACHE:-{DEFAULT_CAMELYON_CACHE_EXPR}}}:/data/cache/camelyon16/slides:rw
    environment:
      - PYTHONUNBUFFERED=1
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 8G
        reservations:
          cpus: '1'
          memory: 4G
"""


def _entrypoint() -> str:
    return """#!/bin/bash
set -euo pipefail

MANIFEST=/opt/task_manifest.json
DEST=/data/slide/current

python3 - <<'PY'
import json
import os
import shutil
import urllib.request
from pathlib import Path

manifest = json.loads(Path("/opt/task_manifest.json").read_text(encoding="utf-8"))
dest = Path("/data/slide/current")
dest.mkdir(parents=True, exist_ok=True)

subset = manifest["subset"]
extension = manifest["slide_extension"]
download_url = manifest["download_url"]

if subset == "tcga":
    cache_root = Path("/data/cache/tcga")
    cache_name = f"{manifest['source_file_id']}{extension}"
else:
    cache_root = Path("/data/cache/camelyon16/slides")
    cache_name = f"{manifest['source_slide_name']}{extension}"

cache_root.mkdir(parents=True, exist_ok=True)
cached_path = cache_root / cache_name
lock_path = cache_root / f"{cache_name}.lock"

with lock_path.open("w") as lock_file:
    import fcntl
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
    if not cached_path.exists() or cached_path.stat().st_size == 0:
        tmp_path = cached_path.with_suffix(cached_path.suffix + ".part")
        with urllib.request.urlopen(download_url, timeout=600) as response, tmp_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        tmp_path.replace(cached_path)

public_manifest = {
    "task_id": manifest["task_id"],
    "subset": manifest["subset"],
    "tile_size": manifest["tile_size"],
    "analysis_downsample": manifest["analysis_downsample"],
    "slide_path": f"/data/slide/current/slide{extension}",
}
slide_dest = dest / f"slide{extension}"
if slide_dest.exists() or slide_dest.is_symlink():
    slide_dest.unlink()
os.symlink(cached_path, slide_dest)
(dest / "manifest.json").write_text(json.dumps(public_manifest, indent=2) + "\\n", encoding="utf-8")
PY

exec "$@"
"""


def _test_sh() -> str:
    return """#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier /logs/artifacts

python /tests/verify_meta_task.py \
  --submission /workspace/submission.json \
  --answer-key /tests/task_answer_key.json \
  --reward-json /logs/verifier/reward.json \
  --results-json /logs/verifier/meta_results.json \
  --error-analysis-file /logs/artifacts/error_analysis.json
"""


def _copy_runtime_workspace(target_workspace: Path) -> None:
    scripts_dir = target_workspace / "scripts"
    if scripts_dir.exists():
        shutil.rmtree(scripts_dir)
    shutil.copytree(RUNTIME_DIR, scripts_dir)


def _copy_self_contained_test_files(target_tests: Path) -> None:
    target_tests.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT_DIR / "harbor_evaluator.py", target_tests / "harbor_evaluator.py")
    shutil.copyfile(SCRIPT_DIR / "harbor_evaluator.py", target_tests / "evaluator.py")
    shutil.copyfile(SCRIPT_DIR / "verify_meta_task.py", target_tests / "verify_meta_task.py")
    (target_tests / "test.sh").write_text(_test_sh(), encoding="utf-8")
    (target_tests / "test.sh").chmod(0o755)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _generate_task(row: dict[str, Any], output_root: Path, cache_root: Path) -> None:
    task_dir = output_root / str(row["task_name"])
    if task_dir.exists():
        shutil.rmtree(task_dir)
    (task_dir / "environment" / "workspace").mkdir(parents=True, exist_ok=True)
    (task_dir / "tests").mkdir(parents=True, exist_ok=True)

    workspace_dir = task_dir / "environment" / "workspace"
    tests_dir = task_dir / "tests"
    env_dir = task_dir / "environment"

    benchmark_tasks = [build_public_task_row(row)]
    submission = [build_submission_row(row)]
    answer_key = _answer_key_rows(row, cache_root)
    runtime_manifest = build_runtime_manifest(row)

    (task_dir / "README.md").write_text(_task_readme(row), encoding="utf-8")
    (task_dir / "instruction.md").write_text(_instruction_md(row), encoding="utf-8")
    (task_dir / "task.toml").write_text(_task_toml(row), encoding="utf-8")

    _write_json(workspace_dir / "benchmark_tasks.json", benchmark_tasks)
    _write_json(workspace_dir / "submission.json", submission)
    (workspace_dir / "README.md").write_text(_workspace_readme(row), encoding="utf-8")
    _copy_runtime_workspace(workspace_dir)

    (env_dir / "Dockerfile").write_text(_dockerfile(), encoding="utf-8")
    (env_dir / "docker-compose.yaml").write_text(_docker_compose(), encoding="utf-8")
    (env_dir / "entrypoint.sh").write_text(_entrypoint(), encoding="utf-8")
    (env_dir / "entrypoint.sh").chmod(0o755)
    _write_json(env_dir / "task_manifest.json", runtime_manifest)

    _copy_self_contained_test_files(tests_dir)
    _write_json(tests_dir / "task_answer_key.json", answer_key)


def main() -> None:
    args = _parse_args()
    rows = _load_all_tasks(args)
    if args.output_root.exists():
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)
    cache_root = args.hidden_cache_root.expanduser().resolve()
    for row in rows:
        _generate_task(row, args.output_root, cache_root)
    print(
        json.dumps(
            {
                "benchmark": BENCHMARK_NAME,
                "task_count": len(rows),
                "output_root": str(args.output_root),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
