# EHRSQL Harbor Task Scripts

This directory contains scripts for integrating EHRSQL (a text-to-SQL benchmark on EHR databases) into the Harbor framework.

## Overview

EHRSQL is a large-scale benchmark of text-to-SQL question answering over Electronic Health Records, with questions from two databases:
- **MIMIC-III**: 2,239 valid tasks + 1,786 test tasks
- **eICU**: 1,117 valid tasks + 1,792 test tasks

Total: ~5,900 tasks across both databases.

## Canonical Files

| File | Purpose |
|---|---|
| `normalization.py` | Task normalization helpers (load, map, build instructions) |
| `generate_harbor_tasks.py` | Main Harbor artifact generator |
| `harbor_evaluator.py` | SQL execution-based evaluation logic |
| `verify_meta_task.py` | Harbor verifier script (called after agent completion) |
| `setup.sh` | Download and validate EHRSQL source data |

## Quick Start

The `run_and_evaluate.sh` script handles data download, task generation, Harbor execution, and result aggregation in one command:

```bash
bash scripts/ehrsql/run_and_evaluate.sh jobs/ehrsql_mimic_iii_test_meta.yaml
bash scripts/ehrsql/run_and_evaluate.sh jobs/ehrsql_eicu_valid_meta.yaml -m gpt-5.1-codex-mini --ak reasoning_effort=low
```

Or via the top-level entry point:

```bash
bash medcli_evaluate.sh --task ehrsql --config jobs/ehrsql_eicu_test_meta.yaml --model gpt-5.3-codex
```

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

We can run the command below to generate per-dataset validation/test task. Because the task data can be huge, we sample 250 examples and we divide it into one-example-per-subtask by specifying split_task_by_n argument to 250. This is in line with the harbor framework requirements. 

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \   
  --output-root tasks/ehrsql/mimic_iii_valid/ \
  --valid-json scripts/ehrsql/assets/mimic_iii/valid.json --split_task_by_n 250 --sample-size 250

uv run python scripts/ehrsql/generate_harbor_tasks.py \   
  --output-root tasks/ehrsql/mimic_iii_test/ \
  --valid-json scripts/ehrsql/assets/mimic_iii/test.json --split_task_by_n 250 --sample-size 250

uv run python scripts/ehrsql/generate_harbor_tasks.py \   
  --output-root tasks/ehrsql/eicu_test/ \
  --valid-json scripts/ehrsql/assets/eicu/test.json --split_task_by_n  250 --sample-size 250

uv run python scripts/ehrsql/generate_harbor_tasks.py \   
  --output-root tasks/ehrsql/eicu_valid/ \
  --valid-json scripts/ehrsql/assets/eicu/valid.json --split_task_by_n  250 --sample-size 250
```

This generates subtasks from the dataset, each subtask contains
- `tasks/ehrsql/mimic_iii_valid/worker_{}/task.toml` — Harbor configuration
- `tasks/ehrsql/mimic_iii_valid/worker_{}/instruction.md` — Agent instructions
- `tasks/ehrsql/mimic_iii_valid/worker_{}/benchmark_tasks.json` — Public task list (2,239 or custom count)
- `tasks/ehrsql/mimic_iii_valid/worker_{}/environment/workspace/` — Agent workspace with SQL primitives
- `tasks/ehrsql/mimic_iii_valid/worker_{}/tests/task_answer_key.json` — Hidden answer keys

### 3. Run with Harbor with parallelization on all subtasks

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run harbor run -c jobs/ehrsql_mimic_iii_valid_meta.yaml
uv run harbor run -c jobs/ehrsql_mimic_iii_test_meta.yaml
uv run harbor run -c jobs/ehrsql_eicu_valid_meta.yaml
uv run harbor run -c jobs/ehrsql_eicu_test_meta.yaml
```

### 4. Run evaluation aggregation over all subtasks

After all workers complete, aggregate submissions and compute the overall score:

```bash
uv run python scripts/ehrsql/aggregate_worker_submissions.py \
  --run-dir results/harbor/ehrsql/mimic_iii_valid/<timestamp> \
  --db-dir scripts/ehrsql/assets

uv run python scripts/ehrsql/aggregate_worker_submissions.py \
  --run-dir results/harbor/ehrsql/mimic_iii_test/<timestamp> \
  --db-dir scripts/ehrsql/assets

uv run python scripts/ehrsql/aggregate_worker_submissions.py \
  --run-dir results/harbor/ehrsql/eicu_valid/<timestamp> \
  --db-dir scripts/ehrsql/assets

uv run python scripts/ehrsql/aggregate_worker_submissions.py \
  --run-dir results/harbor/ehrsql/eicu_test/<timestamp> \
  --db-dir scripts/ehrsql/assets
```

This script:
1. Finds all `worker_*/artifacts/submission.json` files in the run directory
2. Merges them into a single `merged_submission.json`
3. Merges per-worker answer keys if no top-level answer key exists
4. Runs `harbor_evaluator.py` to compute metrics against the gold SQL
5. Outputs `merged_evaluation.json` with pass@1, answerability F1, and execution F1

You can also pass multiple run directories if workers are spread across separate runs:

```bash
uv run python scripts/ehrsql/aggregate_worker_submissions.py \
  --run-dir results/harbor/ehrsql/mimic_iii_valid/<timestamp1> \
              results/harbor/ehrsql/mimic_iii_valid/<timestamp2> \
  --db-dir scripts/ehrsql/assets
```

If `--run-dir` is omitted, the script auto-detects the latest run directory.

## Harbor Task Structure

### Generated Files

```
tasks/ehrsql/mimic_III_valid/worker_{}
├── task.toml                      # Harbor meta-task config
├── instruction.md                 # Agent-facing instructions
├── benchmark_tasks.json           # Public task definitions
├── environment/
│   ├── Dockerfile                 # Agent container image
│   └── workspace/
│       ├── submission.json        # Agent fills this with answers
│       ├── benchmark_tasks.json   # (copy of root)
│       └── scripts/primitives/
│           ├── inspect_schema.py  # Query database schema
│           └── execute_sql.py     # Execute SQL queries
└── tests/
    ├── task_answer_key.json       # Hidden answer keys
    └── verify_meta_task.py        # Verifier script
```

### Evaluation

The verifier (`verify_meta_task.py`):
1. Loads agent's submission from `/workspace/submission.json`
2. Loads answer keys from `/tests/task_answer_key.json`
3. Executes both gold SQL and predicted SQL
4. Compares result sets for equivalence
5. Outputs metrics to `/logs/verifier/`:
   - `reward.txt` — pass@1 score (0.0-1.0)
   - `meta_results.json` — full evaluation results

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
job configurations for each dataset-split combination is found in jobs/ehrsql_{data}_{split}_meta.yaml


## References

- **EHRSQL paper**: https://arxiv.org/abs/2501.14654
- **EHRSQL GitHub**: https://github.com/glee4810/EHRSQL
- **Harbor docs**: See CLAUDE.md for Harbor framework details
