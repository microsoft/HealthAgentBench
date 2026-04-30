# Tumor Area Selection

You are working inside a pathology task environment that contains:

- the current whole-slide image at `/data/slide/current/slide.*`
- a public task row in `/workspace/benchmark_tasks.json`
- an editable single-row submission in `/workspace/submission.json`
- pathology helper scripts under `/workspace/scripts/primitives/`

Tool examples:
- `python /workspace/scripts/primitives/get_slide_thumbnail.py --max-size 1024`
- `python /workspace/scripts/primitives/get_tissue_mask.py`
- `python /workspace/scripts/primitives/sample_tiles.py --count 20`
- `python /workspace/scripts/primitives/get_tile.py --x 12 --y 44`
- `python /workspace/scripts/primitives/get_region.py --x 12 --y 44 --width 3 --height 3 --max-size 1536`

The benchmark analysis grid uses 256x256 tiles at downsample 16.

## Your Task

Complete the tumor area selection task by deciding whether tumor is present on this slide and predicting the set of all tumor tiles on the benchmark grid.

Submission requirements:
- set `contains_tumor` to `true` if you believe any tumor is present, else `false`
- populate `predicted_tumor_tiles` with dictionaries of the form `{ "x": <int>, "y": <int> }`
- include every tile you believe contains tumor
- non-tissue tiles should be treated as non-tumor
- do not modify `task_id` or `instruction`

## Important Rules

- Work autonomously until the submission is complete.
- Do not train models or fine-tune weights.
- Use the provided helper scripts and your own reasoning over their outputs.
- Update `submission.json` with a JSON-aware tool such as Python.
