# Tumor Area Selection

You are working inside a pathology task environment that contains:

- the current whole-slide H&E image at `/data/slide/current/slide.tif` (a multi-resolution pyramidal TIFF), with grid parameters in `/data/slide/current/manifest.json`
- a public task row in `/workspace/benchmark_tasks.json`
- an editable single-row submission in `/workspace/submission.json`

## Analysis grid

The benchmark analysis grid uses 256x256 tiles at downsample 16, so each grid tile spans 4096x4096 full-resolution (level-0) pixels (`4096 = 256*16`). Grid tile `(x, y)` covers the level-0 region with horizontal extent `x*4096` to `(x+1)*4096` (x = column) and vertical extent `y*4096` to `(y+1)*4096` (y = row). The grid has `ceil(slide_width/4096)` columns (indexed by x) and `ceil(slide_height/4096)` rows (indexed by y), where `slide_width` and `slide_height` are the level-0 dimensions. Report tumor tiles using these integer `(x, y)` grid coordinates.

## What counts as a tumor tile

A tile counts as tumor when tumor covers at least 20% of its valid in-slide area (`tumor_threshold` = 0.2 in `benchmark_tasks.json`).

## Your Task

Find the fixed-grid tiles that contain metastatic carcinoma. Localize tumor from the provided H&E images. Identify all and only the tumor tiles on the analysis grid and record them in `/workspace/submission.json`:

- set `contains_tumor` to `true` if the slide contains any tumor tile, otherwise `false`
- populate `predicted_tumor_tiles` with dictionaries of the form `{ "x": <int>, "y": <int> }`, one per tumor tile (leave it empty if you believe the slide has no tumor)
- include every tile you believe is a tumor tile and do not include tiles you believe are not
- do not modify `task_id`

Your submission is scored by tile-level F1 between `predicted_tumor_tiles` and the gold tumor tiles derived from expert annotations. The task passes when F1 is at least 0.9, so both missed tumor tiles and spurious tiles count against you; selecting every tissue tile will not pass.

## Resources

You have 1.5 hours to complete the task. There is no internet access beyond the
model API. The container is configured for 2 CPUs, 8 GiB of memory, 20 GiB of disk,
and no GPU. System tools may report host resources, not these limits.
