# `pathology_tumor_area_selection_slide_0005`

This is one of 10 `pathology_tumor_area_selection_*` tasks in the **Pathology Tumor Area Selection** category of [HealthAgentBench](../../README.md).

Given one whole-slide H&E pathology image, predict the set of tiles / regions that contain tumor and write the selected tumor region. Gold tumor masks are derived from expert annotations.

**Success criteria:** predicted tumor tiles match the gold region with tile-level F1 at or above 0.9.

## Run this task

```bash
uv run harbor run \
  --path tasks/pathology_tumor_area_selection_slide_0005 \
  --agent claude-code \
  --model claude-opus-4-8 \
  --agent-kwarg reasoning_effort=xhigh \
  --agent-kwarg disallowed_tools="WebSearch WebFetch" \
  --n-attempts 3 --n-concurrent 5
```

## Run the whole Pathology Tumor Area Selection category

Point `--path` at `tasks/` and glob the category name with `--include-task-name` (quote it so the shell doesn't expand the `*`):

```bash
uv run harbor run \
  --path tasks \
  --include-task-name "pathology_tumor_area_selection_*" \
  --agent claude-code \
  --model claude-opus-4-8 \
  --agent-kwarg reasoning_effort=xhigh \
  --agent-kwarg disallowed_tools="WebSearch WebFetch" \
  --n-attempts 3 --n-concurrent 5
```

## Data & references

Uses public whole-slide H&E pathology images bundled in the task environment.

- Camelyon 16 Challenge <https://camelyon16.grand-challenge.org/>
