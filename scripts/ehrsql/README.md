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

## Workflow

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

**Generate with all validation set tasks (2,239 tasks):**

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql \
  --valid-json scripts/ehrsql/assets/mimic_iii/valid.json scripts/ehrsql/assets/eicu/valid.json
```

**Or with default strategy:**

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql
```

**Or with specific task IDs:**

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql \
  --selected-task-ids task_id1,task_id2,task_id3
```

This generates:
- `tasks/ehrsql/task.toml` — Harbor configuration
- `tasks/ehrsql/instruction.md` — Agent instructions
- `tasks/ehrsql/benchmark_tasks.json` — Public task list (2,239 or custom count)
- `tasks/ehrsql/environment/workspace/` — Agent workspace with SQL primitives
- `tasks/ehrsql/tests/task_answer_key.json` — Hidden answer keys

### 3. Run with Harbor

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run harbor run -c jobs/ehrsql_meta.yaml
```

## Harbor Task Structure

### Generated Files

```
tasks/ehrsql/
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

## Key Design Decisions

1. **Task Type**: EHRSQL is `factual_qa` — Q&A over EHRs (SQL is implementation detail)
2. **Answer Format**: Agent returns SQL string (or "null" for unanswerable)
3. **Evaluation**: Execute both gold and predicted SQL, compare result sets (set-based, not string-based)
4. **Unanswerable Tasks**: ~8.8% marked `is_impossible: true`; agent should return "null"
5. **Databases**: Two databases (MIMIC-III, eICU) distinguished by `db_id` field


## Multi-Dataset Experiments

Run EHRSQL evaluation across multiple dataset splits (MIMIC-III and eICU, validation and test) with separate output directories for easy comparison.

### Sampling from Specific Datasets

When you provide `--valid-json` or `--test-json`, tasks are randomly sampled (deterministic with fixed seed=42):

```bash
# Sample 100 random tasks from MIMIC-III validation set
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql_mimic_iii_valid \
  --valid-json scripts/ehrsql/assets/mimic_iii/valid.json \
  --sample-size 100

# Sample 100 random tasks from MIMIC-III test set
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql_mimic_iii_test \
  --test-json scripts/ehrsql/assets/mimic_iii/test.json \
  --sample-size 100

# Sample 100 random tasks from eICU validation set
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql_eicu_valid \
  --valid-json scripts/ehrsql/assets/eicu/valid.json \
  --sample-size 100

# Sample 100 random tasks from eICU test set
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root tasks/ehrsql_eicu_test \
  --test-json scripts/ehrsql/assets/eicu/test.json \
  --sample-size 100
```

Output structure:
```
tasks/
  ehrsql_mimic_iii_valid/
  ehrsql_mimic_iii_test/
  ehrsql_eicu_valid/
  ehrsql_eicu_test/
```

### Creating Job Configurations

Create `jobs/ehrsql_mimic_iii_valid_meta.yaml`:
```yaml
jobs_dir: results/harbor/ehrsql_mimic_iii_valid
n_attempts: 1
orchestrator:
  type: local
  n_concurrent_trials: 1
environment:
  type: docker
  force_build: true
  env:
    - CODEX_AUTH_JSON=${CODEX_AUTH_JSON}
agents:
  - import_path: medcli.agents.harbor.installed.codex:Codex
    model_name: gpt-5.1-codex-mini
datasets:
  - path: tasks
    task_names:
      - ehrsql_mimic_iii_valid
artifacts:
  - /workspace/submission.json
```

Repeat for other splits (replace `mimic_iii_valid` with `mimic_iii_test`, `eicu_valid`, `eicu_test` in both the YAML filename, `jobs_dir`, and `task_names`).

### Running Experiments

Run all splits in parallel:
```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

uv run harbor run -c jobs/ehrsql_mimic_iii_valid_meta.yaml &
uv run harbor run -c jobs/ehrsql_mimic_iii_test_meta.yaml &
uv run harbor run -c jobs/ehrsql_eicu_valid_meta.yaml &
uv run harbor run -c jobs/ehrsql_eicu_test_meta.yaml &

wait
echo "All experiments completed"
```

Or run sequentially:
```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

for split in mimic_iii_valid mimic_iii_test eicu_valid eicu_test; do
  uv run harbor run -c jobs/ehrsql_${split}_meta.yaml
done
```

### Comparing Results

Results are organized by task split:
```
results/harbor/
  ehrsql_mimic_iii_valid/          # Results for MIMIC-III validation
    {timestamp}/
      {task_id}__ABC123/
        meta_results.json
        detailed_results.json
  ehrsql_mimic_iii_test/           # Results for MIMIC-III test
    {timestamp}/
      ...
  ehrsql_eicu_valid/               # Results for eICU validation
    {timestamp}/
      ...
  ehrsql_eicu_test/                # Results for eICU test
    {timestamp}/
      ...
```

Extract and compare accuracy across splits:
```bash
echo "MIMIC-III valid:  $(jq '.pass_at_1' results/harbor/ehrsql_mimic_iii_valid/*/ehrsql_mimic_iii_valid__*/meta_results.json | head -1)"
echo "MIMIC-III test:   $(jq '.pass_at_1' results/harbor/ehrsql_mimic_iii_test/*/ehrsql_mimic_iii_test__*/meta_results.json | head -1)"
echo "eICU valid:       $(jq '.pass_at_1' results/harbor/ehrsql_eicu_valid/*/ehrsql_eicu_valid__*/meta_results.json | head -1)"
echo "eICU test:        $(jq '.pass_at_1' results/harbor/ehrsql_eicu_test/*/ehrsql_eicu_test__*/meta_results.json | head -1)"
```

## Sampling Strategy Notes

- **Random sampling** (when `--valid-json` / `--test-json` provided): Draws a random sample of specified size from the provided JSON file. Deterministic with seed=42.
- **Default strategy** (when no JSON files provided): Stratified sampling by database and importance level (balanced coverage).
- **Explicit task IDs** (when `--selected-task-ids` provided): Uses exact task IDs, no sampling applied.

## Troubleshooting

**SQLite database not found**
- Ensure `scripts/ehrsql/assets/mimic_iii/mimic_iii.sqlite` and `scripts/ehrsql/assets/eicu/eicu.sqlite` exist
- Download from Google Drive links above

**Primitivescripts fail in container**
- Check that `/scripts/ehrsql/assets/` is mounted in Harbor container
- Verify database files are readable (chmod +r)

**Evaluation returns all failures**
- Check database connectivity: `sqlite3 scripts/ehrsql/assets/mimic_iii/mimic_iii.sqlite ".tables"`
- Verify answer key is present: `ls -la tasks/ehrsql/tests/task_answer_key.json`

## References

- **EHRSQL paper**: https://arxiv.org/abs/2501.14654
- **EHRSQL GitHub**: https://github.com/glee4810/EHRSQL
- **Harbor docs**: See CLAUDE.md for Harbor framework details
