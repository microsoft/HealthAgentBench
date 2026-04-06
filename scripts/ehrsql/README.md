# EHRSQL Harbor Task Scripts

This directory contains scripts for integrating EHRSQL (a text-to-SQL benchmark on EHR databases) into the Harbor framework.

## Overview

EHRSQL is a large-scale benchmark of text-to-SQL question answering over Electronic Health Records, with questions from two databases:
- **MIMIC-III**: 2,239 valid tasks + 1,786 test tasks
- **eICU**: 1,117 valid tasks + 1,792 test tasks

Total: ~5,900 tasks across both databases.

We also offer a Lite version that covers 250 samples from MIMIC-III and 250 samples from eICU. 

## Canonical Files

| File | Purpose |
|---|---|
| `normalization.py` | Task normalization helpers (load, map, build instructions) |
| `generate_harbor_tasks.py` | Main Harbor artifact generator |
| `harbor_evaluator.py` | SQL execution-based evaluation logic |
| `verify_meta_task.py` | Harbor verifier script (called after agent completion) |
| `setup.sh` | Download and validate EHRSQL source data |


## Workflow (Manual Steps)

### 1. Setup: Download Source Data

```bash
bash scripts/ehrsql/setup.sh
```

This:
- Downloads EHRSQL JSON files from GitHub (valid.json, test.json, tables.json)
- Validates schemas
- Generates SHA256SUMS checksums

**Important**: SQLite databases must be downloaded separately from Google Drive:
- MIMIC-III: https://drive.google.com/file/d/17FkHhaQrmSz5-W2b7WEy90duKfvjBn5x/view?usp=sharing
- eICU: https://drive.google.com/file/d/1JG9DUdeJeuIXShK6DdEJ61NEyPiaGEKZ/view?usp=sharing

Place in:
```
scripts/ehrsql/assets/mimic_iii/mimic_iii.sqlite
scripts/ehrsql/assets/eicu/eicu.sqlite
```

### 2. Generate Harbor Task Artifact

**Generate tasks:**

Run the two commands below consecutively to generate the `ehrsql_lite` dataset (250 MIMIC-III samples + 250 eICU samples). Each example becomes its own Harbor task directory, named `{db_id}_{id}` where `id` is the raw task ID from the source JSON.

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql_lite \
  --input-json scripts/ehrsql/assets/mimic_iii/test.json --split_task_by_n 250 --sample-size 250

uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql_lite \
  --input-json scripts/ehrsql/assets/eicu/test.json --split_task_by_n 250 --sample-size 250
```

This produces a flat directory of 500 task subdirectories under `tasks/ehrsql_lite/`:

```
tasks/ehrsql_lite/
├── mimic_iii_b0cf870ad682fec65dec583c/   # MIMIC-III task
├── mimic_iii_ea2a11ee9365d4ddc5ea34f5/
├── ...
├── eicu_ba95373f025351f7de88a95a/        # eICU task
├── eicu_3247dbf0101727c6e704085b/
└── ...
```

Each task directory contains the standard Harbor meta-task layout (task.toml, instruction.md, environment/, tests/).

### 3. Run with Harbor

Run on MIMIC iii testset

```bash
source .venv/bin/activate && export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)" && uv run harbor run -c jobs/ehrsql_lite_mimic_iii_meta.yaml
```

Run on eicu testset
```bash
source .venv/bin/activate && export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)" && uv run harbor run -c jobs/ehrsql_lite_eicu_meta.yaml
```

The harbor run will also check if sql database is already present in `scripts/ehrsql/assets/`, otherwise, it will download it. 


## Task Format

### Input: Raw EHRSQL JSON

```json
{
  "id": "...",
  "question": "What is the method of intake for clobetasol propionate?",
  "db_id": "mimic_iii",
  "split": "valid",
  "query": "SELECT DISTINCT route FROM prescriptions WHERE drug = '...'",
  "is_impossible": false,
  "importance": "medium",
  ...
}
```

### Output: Harbor Submission Format

```json
{
  "task_id": "ehrsql_mimic_iii_valid_xyz",
  "instruction": "What is the method of intake for clobetasol propionate 0.05% ointment?",
  "final_answer": "SELECT DISTINCT route FROM prescriptions WHERE drug = 'clobetasol propionate 0.05% ointment'",
  "payload": null
}
```

### Creating Job Configurations
job configurations for each dataset-split combination is found in jobs/ehrsql_{data}_meta.yaml


## References

- **EHRSQL paper**: https://arxiv.org/abs/2501.14654
- **EHRSQL GitHub**: https://github.com/glee4810/EHRSQL
- **Harbor docs**: See CLAUDE.md for Harbor framework details
