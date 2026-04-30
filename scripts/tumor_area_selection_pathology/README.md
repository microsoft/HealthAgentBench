# Tumor Area Selection Pathology

This directory contains the Harbor-first integration for the
`tumor_area_selection_pathology` benchmark.

The benchmark has two subsets under one task family:

- `TCGA` slide-level tumor classification over public TCGA tissue-slide H&E
  images.
- `CAMELYON16` tumor-tile set prediction over public lymph-node whole-slide
  images with hidden mask-derived gold tiles.

Each Harbor task is one slide. The agent must use the provided pathology tools
to inspect the slide, reason about tumor presence, and write a structured
prediction to `/workspace/submission.json`.

## Canonical Source and Canonical Runner

- Canonical source manifests:
  - `scripts/tumor_area_selection_pathology/assets/tcga_slide_manifest.json`
  - `scripts/tumor_area_selection_pathology/assets/camelyon16_slide_manifest.json`
- Canonical bootstrap script:
  - `scripts/tumor_area_selection_pathology/setup.sh`
- Canonical Harbor task generator:
  - `scripts/tumor_area_selection_pathology/generate_harbor_tasks.py`
- Canonical runnable task artifact:
  - `tasks/tumor_area_selection_pathology/`
- Canonical evaluator and verifier:
  - `scripts/tumor_area_selection_pathology/harbor_evaluator.py`
  - `scripts/tumor_area_selection_pathology/verify_meta_task.py`
- Canonical pooled metric aggregator:
  - `scripts/tumor_area_selection_pathology/aggregate_metric.py`

## Benchmark Contract

Every generated task uses the same submission schema:

```json
[
  {
    "task_id": "...",
    "instruction": "...",
    "contains_tumor": false,
    "predicted_tumor_tiles": []
  }
]
```

Subset-specific semantics:

- `TCGA`
  - The agent predicts whether the slide contains tumor.
  - `predicted_tumor_tiles` must stay empty.
  - Aggregate metric: slide-level precision / recall / F1.

- `CAMELYON16`
  - The agent predicts whether tumor is present and, if so, the set of all
    grid tiles it believes contain tumor.
  - Tiles are evaluated on a fixed 256x256 grid at the benchmark's fixed
    analysis downsample.
  - A tile is gold-positive if the hidden CAMELYON mask covers at least 20%
    of that tile.
  - Non-tissue tiles are treated as non-tumor.
  - Aggregate metric: tile-level precision / recall / F1.

## Tool Surface

The generated task workspace includes these pathology helpers under
`/workspace/scripts/primitives/`:

- `get_slide_thumbnail.py`
- `get_tile.py`
- `get_region.py`
- `get_tissue_mask.py`
- `score_tissue_content.py`
- `sample_tiles.py`
- `get_neighbor_tiles.py`
- `get_gigapath_attention_map.py`
- `get_topk_attention_tiles.py`
- `classify_tile_tumor_probability.py`

The GigaPath tools use a cached / optional inference path:

- if a precomputed cache exists, they read it
- otherwise, if `HF_TOKEN` is available and the model terms have been accepted,
  they can build the cache lazily
- otherwise, they fall back to a deterministic heuristic ranking and label the
  backend as `heuristic_fallback`

The weak tile-classification helper is always available and uses deterministic
handcrafted morphology features so the benchmark can still run without
foundation-model auth.

## External Cache Layout

This benchmark is designed to keep public slide downloads outside the git repo.
By default, `setup.sh` uses:

- `${HOME}/harbor-cache/tumor_area_selection_pathology/tcga`
- `${HOME}/harbor-cache/tumor_area_selection_pathology/camelyon16/slides`
- `${HOME}/harbor-cache/tumor_area_selection_pathology/camelyon16/masks`
- `${HOME}/harbor-cache/tumor_area_selection_pathology/gigapath`

You can override these with host environment variables before running Harbor:

- `MEDCLI_TUMOR_PATH_TCGA_CACHE`
- `MEDCLI_TUMOR_PATH_CAMELYON_CACHE`
- `MEDCLI_TUMOR_PATH_GIGAPATH_CACHE`
- `MEDCLI_TUMOR_PATH_CACHE_ROOT`

For Harbor runs that need GigaPath model access, provide `HF_TOKEN` from an
external env file rather than committing credentials to the repository.

To precompute GigaPath cache JSON files ahead of Harbor runs:

```bash
HF_TOKEN=... uv run python scripts/tumor_area_selection_pathology/precompute_gigapath_cache.py
```

## Canonical Workflow

From the repository root:

```bash
# 1) Build or refresh deterministic source manifests and create shared caches.
bash scripts/tumor_area_selection_pathology/setup.sh

# Optional: warm the shared slide caches immediately.
bash scripts/tumor_area_selection_pathology/setup.sh --download-slides

# Optional: use a fully external cache root explicitly.
MEDCLI_TUMOR_PATH_CACHE_ROOT=/mnt/benchmark-cache/tumor_area_selection_pathology \
  bash scripts/tumor_area_selection_pathology/setup.sh --download-slides --download-camelyon-masks

# 2) Generate the Harbor task tree.
uv run python scripts/tumor_area_selection_pathology/generate_harbor_tasks.py \
  --output-root tasks/tumor_area_selection_pathology

# 3) Run benchmark-specific tests.
uv run pytest tests/test_tumor_area_selection_pathology_task.py -q

# 4) Run Harbor.
uv run harbor run -c jobs/tumor_area_selection_pathology.yaml
```

## Runtime Data Model

The benchmark uses committed source manifests and lazy public-data download:

- The task generator commits only lightweight metadata and hidden verifier
  fields.
- The task entrypoint downloads a missing slide into a shared host cache on the
  first run of that task family.
- CAMELYON mask files are verifier-only and are downloaded or cached only by
  the verifier path.

This keeps the repository size reasonable while still letting the benchmark run
from public data end to end.

`get_region.py` is intentionally optimized as a pyramid-aware overview tool: it
reads from the closest slide level and caps large region renders, while
`get_tile.py` remains the more precise single-grid-tile inspection path.

## Manual Replay

See `debug/tumor_area_selection_pathology/README.md` for the benchmark-specific
manual replay path.
