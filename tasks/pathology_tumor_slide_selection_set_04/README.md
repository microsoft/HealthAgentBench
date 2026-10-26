# `pathology_tumor_slide_selection_set_04`

This is one of 10 `pathology_tumor_slide_selection_*` tasks in the **Pathology Tumor Slide Selection** category of [HealthAgentBench](../../README.md).

The agent is given 8 whole-slide H&E pathology images under `/data/slides/` (opaque names `slide_1.svs` … `slide_8.svs`). Any number of them, possibly none, are tumor slides; the agent is not told how many. A tumor slide is defined in the instruction as one that contains malignant tumor cells, whether primary or metastatic. The agent must inspect the slides with the preinstalled tooling (the agent phase has no internet access beyond the model API) and list every tumor slide in `/workspace/submission.json`.

**Success criteria:** the submitted `tumor_slides` set exactly matches the set of slides whose hidden label is tumor (binary reward; slide-level precision/recall/F1 are also reported in `metrics.json`).

## Run this task

```bash
uv run harbor run \
  --path tasks/pathology_tumor_slide_selection_set_04 \
  --agent claude-code \
  --model claude-opus-4-8 \
  --agent-kwarg reasoning_effort=xhigh \
  --agent-kwarg disallowed_tools="WebSearch WebFetch" \
  --n-attempts 3 --n-concurrent 5
```

## Run the whole Pathology Tumor Slide Selection category

Point `--path` at `tasks/` and glob the category name with `--include-task-name` (quote it so the shell doesn't expand the `*`):

```bash
uv run harbor run \
  --path tasks \
  --include-task-name "pathology_tumor_slide_selection_*" \
  --agent claude-code \
  --model claude-opus-4-8 \
  --agent-kwarg reasoning_effort=xhigh \
  --agent-kwarg disallowed_tools="WebSearch WebFetch" \
  --n-attempts 3 --n-concurrent 5
```

## Data & references

Uses public whole-slide H&E frozen tissue-section images (TCGA top/bottom-section slides, not FFPE diagnostic slides), downloaded at run time by the task's one-shot `bootstrap` service from the NCI Genomic Data Commons (no credentials required) into the shared cache `assets/tumor_slide_selection_pathology/assets/raw_cache/`. Slide-level labels are verifier-only and require an unambiguous pathologist review recorded in GDC for every slide: tumor slides are Primary Tumor / Metastatic samples whose pathologist-reviewed `percent_tumor_cells` is greater than 0, and normal slides are Solid Tissue Normal samples whose reviewed `percent_tumor_cells` is exactly 0. Slides without a recorded review are excluded from the pool.

- NCI Genomic Data Commons <https://portal.gdc.cancer.gov/>
