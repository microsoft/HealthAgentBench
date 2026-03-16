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
data/ehrsql/mimic_iii/mimic_iii.sqlite
data/ehrsql/eicu/eicu.sqlite
```

### 2. Generate Harbor Task Artifact

**Generate with all validation set tasks (2,239 tasks):**

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql \
  --valid-json data/ehrsql/mimic_iii/valid.json data/ehrsql/eicu/valid.json
```

**Or with default strategy (8 representative tasks):**

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql
```

**Or with specific task IDs:**

```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql \
  --selected-task-ids task_id1,task_id2,task_id3
```

This generates:
- `harbor_tasks/ehrsql/task.toml` — Harbor configuration
- `harbor_tasks/ehrsql/instruction.md` — Agent instructions
- `harbor_tasks/ehrsql/benchmark_tasks.json` — Public task list (2,239 or custom count)
- `harbor_tasks/ehrsql/environment/workspace/` — Agent workspace with SQL primitives
- `harbor_tasks/ehrsql/tests/task_answer_key.json` — Hidden answer keys

### 3. Run with Harbor

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run harbor run -c jobs/ehrsql_meta.yaml
```

## Harbor Task Structure

### Generated Files

```
harbor_tasks/ehrsql/
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

## Customization

### Selection Strategies

**Default (8 representative tasks):**
One task per (database, difficulty) combination for quick validation.
```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql
```

**All Validation Tasks (2,239 tasks):**
Complete benchmark on validation set (MIMIC-III + eICU).
```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql \
  --valid-json data/ehrsql/mimic_iii/valid.json data/ehrsql/eicu/valid.json
```

**All Test Tasks (3,578 tasks):**
Complete benchmark on test set (held-out evaluation).
```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql \
  --test-json data/ehrsql/mimic_iii/test.json data/ehrsql/eicu/test.json
```

**Specific Tasks:**
Hand-select individual tasks by ID.
```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql \
  --selected-task-ids task1,task2,task3
```

## Troubleshooting

**SQLite database not found**
- Ensure `data/ehrsql/mimic_iii/mimic_iii.sqlite` and `data/ehrsql/eicu/eicu.sqlite` exist
- Download from Google Drive links above

**Primitivescripts fail in container**
- Check that `/data/ehrsql/` is mounted in Harbor container
- Verify database files are readable (chmod +r)

**Evaluation returns all failures**
- Check database connectivity: `sqlite3 data/ehrsql/mimic_iii/mimic_iii.sqlite ".tables"`
- Verify answer key is present: `ls -la harbor_tasks/ehrsql/tests/task_answer_key.json`

## References

- **EHRSQL paper**: https://arxiv.org/abs/2501.14654
- **EHRSQL GitHub**: https://github.com/glee4810/EHRSQL
- **Harbor docs**: See CLAUDE.md for Harbor framework details
