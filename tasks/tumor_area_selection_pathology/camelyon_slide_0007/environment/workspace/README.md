# tumor_area_selection_pathology

Subset: `camelyon16`

Files:
- `benchmark_tasks.json`: public task metadata
- `submission.json`: single-row structured output to fill in
- `scripts/primitives/`: pathology helper scripts

Useful helper examples:
- `python /workspace/scripts/primitives/get_slide_thumbnail.py --max-size 1024`
- `python /workspace/scripts/primitives/sample_tiles.py --count 20`
- `python /workspace/scripts/primitives/get_tile.py --x 10 --y 12`
- `python /workspace/scripts/primitives/classify_tile_tumor_probability.py --x 10 --y 12`
- `python /workspace/scripts/primitives/get_gigapath_attention_map.py --max-tiles 256`

Always update `submission.json` with a JSON-aware tool, not raw text editing.
