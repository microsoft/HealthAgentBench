# How to Add Tasks to the MedCLI Codebase

Adding a task to MedCLI requires three main steps. **MedAgentBench** and **EHRSQL** serve as canonical examples.

---

## Step 1: Data Preparation

**Goal**: Prepare raw task data as JSON file(s) using a setup script.

### What to Do

Create a **setup script** at `scripts/<task-name>/setup.sh` that:
1. Downloads raw task JSON from an external source (GitHub, Box, etc.)
2. Validates the schema
3. Outputs JSON files to `data/<task-name>/`

Run it once to prepare the data:
```bash
bash scripts/<task-name>/setup.sh
```

### Raw Task Format

Each task object should contain:
- `id` — unique task identifier (e.g., `"task1_1"`, `"task2_5"`)
- `instruction` — the user-facing question/prompt
- `context` — optional background information
- `sol` — list of acceptable solutions (for grading)
- Domain-specific fields (e.g., `eval_MRN` for medical tasks, `db_id` for SQL tasks)

### Example Task

```json
{
  "id": "task1_1",
  "instruction": "What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29?",
  "context": "",
  "sol": ["S6534835"],
  "eval_MRN": "S6534835"
}
```

### Real Examples
- **MedAgentBench setup**: `scripts/medagentbench/setup.sh` → Downloads from GitHub + validates + backfills solutions
- **EHRSQL setup**: `scripts/ehrsql/setup.sh` → Downloads task JSON from GitHub + validates schemas

---

## Step 2: Generator Implementation

**Goal**: Create a `generate_harbor_tasks.py` script that builds the complete Harbor task artifact.

The generator is responsible for creating everything in `harbor_tasks/<task-name>/`:
- `task.toml` — Harbor configuration
- `instruction.md` — Agent-facing instructions
- `benchmark_tasks.json` — Normalized task list
- `environment/Dockerfile` — Container definition
- `environment/workspace/` — Workspace files (submission template, helper scripts, etc.)
- `tests/verify_meta_task.py` — Verifier logic
- `tests/task_answer_key.json` — Hidden ground-truth answers

### What to Implement

Your generator should:

1. **Create a normalization module** at `scripts/<task-name>/normalization.py` with these functions:
   ```python
   def load_raw_tasks(path: Path) -> list[dict]:
       """Load raw JSON tasks"""

   def normalize_harbor_task(task: dict) -> dict:
       """Convert raw task to Harbor format (task_id, instruction, final_answer, payload)"""

   def build_harbor_answer_key(task: dict) -> dict:
       """Extract hidden validation data"""

   def build_instruction(base_instruction: str, context: str) -> str:
       """Format user-facing instruction"""

   def infer_group(task_id: str) -> str:
       """Extract task group from ID (e.g., 'task1' from 'task1_5')"""

   def default_selected_task_ids(raw_tasks: list) -> list[str]:
       """Return default slice of tasks (one-per-group, smoke test, etc.)"""
   ```

2. **Create an evaluator module** at `scripts/<task-name>/harbor_evaluator.py` with:
   ```python
   def evaluate_submission_rows(rows: list[dict]) -> dict:
       """Compare submitted answers to answer key, return pass/fail per task"""
   ```

3. **Create the generator script** at `scripts/<task-name>/generate_harbor_tasks.py` that:
   - Parses CLI args (input JSON, output directory, optional task selection)
   - Loads and normalizes raw tasks
   - Generates Harbor files using helper functions like:
     - `_instruction_md()` — generates instruction.md
     - `_task_toml()` — generates task.toml
     - `_primitive_scripts()` — generates domain-specific helper scripts
     - `_verify_meta_task_py()` — generates verifier template
     - `_write_meta_task()` — writes all files to disk

### Key Principle: Generator is Source of Truth

⚠️ **Do NOT manually edit files in `harbor_tasks/<task-name>/`** — they are generated artifacts.

To modify the Harbor task:
- Change helper scripts? → Edit `_primitive_scripts()` in the generator
- Change instructions? → Edit `_instruction_md()` in the generator
- Change task config? → Edit `_task_toml()` in the generator
- Change evaluation logic? → Edit the evaluator module at `scripts/<task-name>/harbor_evaluator.py`

After modifying the generator, regenerate:
```bash
uv run python scripts/<task-name>/generate_harbor_tasks.py \
  --input-json data/<task-name>/raw_tasks.json \
  --output-root harbor_tasks/<task-name>
```

### Real Examples
- **MedAgentBench**: `scripts/medagentbench/generate_harbor_tasks.py` (7 read helpers + 4 write helpers, FHIR-based)
- **EHRSQL**: `scripts/ehrsql/generate_harbor_tasks.py` (2 SQL helpers, database-agnostic)

---

## Step 3: Documentation

**Goal**: Update project docs and create setup guides.

### What to Update

1. **`README.md`**:
   - Add benchmark to "Task Sources" section
   - Add to "Project Structure"
   - Add example generation and run commands under "Harbor Usage"

2. **`CLAUDE.md` and `AGENTS.md`** (keep in sync):
   - Add benchmark to "Repository Layout" section
   - Add generation and run example commands to "Harbor Usage"

3. **`scripts/<task-name>/README.md`** (new file):
   - How to download/prepare raw data
   - Generator script arguments and customization options
   - Troubleshooting guide
   - References to original benchmark paper/repo

4. **`jobs/<task-name>_meta.yaml`** (new file):
   - Harbor job configuration for running the benchmark

### Example Changes
- **MedAgentBench docs**: `scripts/medagentbench/README.md`
- **EHRSQL docs**: `scripts/ehrsql/README.md`

---

## Workflow Checklist

```bash
# 0. Prepare and validate raw data
bash scripts/<task-name>/setup.sh
# This downloads raw JSON and validates schema
# Outputs: data/<task-name>/raw_tasks.json (or task splits)

# 1. Implement normalization
# → scripts/<task-name>/normalization.py

# 2. Implement evaluator
# → scripts/<task-name>/harbor_evaluator.py

# 3. Implement generator
# → scripts/<task-name>/generate_harbor_tasks.py

# 4. Generate Harbor task
uv run python scripts/<task-name>/generate_harbor_tasks.py \
  --input-json data/<task-name>/raw_tasks.json \
  --output-root harbor_tasks/<task-name>

# 5. Create job config
# → jobs/<task-name>_meta.yaml

# 6. Update documentation
# → README.md, CLAUDE.md, AGENTS.md, scripts/<task-name>/README.md

# 7. Run the task (after setting up auth)
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run harbor run -c jobs/<task-name>_meta.yaml
```

---

## Key Design Principles

- **Generator is source of truth**: All Harbor task files are generated. Modify the generator, not the artifacts.
- **Separation of concerns**: Raw data → normalization → generation → environment → evaluation
- **Self-contained tasks**: Each Harbor task directory is independently runnable with all required files bundled.
- **Hidden answer keys**: Ground-truth answers stored separately from agent-visible files for integrity.
- **Primitives over ad-hoc code**: Use domain-specific helper scripts, not arbitrary shell commands.

---

## Real Examples to Reference

### MedAgentBench (FHIR-based EHR tasks)
- Raw data: `data/medagentbench/test_data_v2.json`
- Generator: `scripts/medagentbench/generate_harbor_tasks.py`
- Normalization: `scripts/medagentbench/normalization.py`
- Evaluator: `scripts/medagentbench/harbor_evaluator.py`
- Generated task: `harbor_tasks/medagentbench/`
- Setup guide: `scripts/medagentbench/README.md`

### EHRSQL (Text-to-SQL tasks)
- Raw data: `data/ehrsql/mimic_iii/valid.json`, `data/ehrsql/eicu/valid.json`
- Generator: `scripts/ehrsql/generate_harbor_tasks.py`
- Normalization: `scripts/ehrsql/normalization.py`
- Evaluator: `scripts/ehrsql/harbor_evaluator.py`
- Generated task: `harbor_tasks/ehrsql/`
- Setup guide: `scripts/ehrsql/README.md`

---

## Appendix: Generated Harbor Task Structure

After running the generator, your `harbor_tasks/<task-name>/` directory contains:

```
harbor_tasks/<task-name>/
├── task.toml                          # Meta-task config
├── instruction.md                     # Agent-facing instructions
├── benchmark_tasks.json               # Reference copy of tasks
│
├── environment/
│   ├── Dockerfile                     # Container definition
│   ├── docker-compose.yaml            # (optional) Backend services
│   └── workspace/
│       ├── README.md                  # Workspace guide
│       ├── benchmark_tasks.json       # Tasks for agent to read
│       ├── submission.json            # Template for agent to fill in
│       └── scripts/primitives/        # Domain-specific helper scripts
│
└── tests/
    ├── test.sh                        # Harbor test entry point
    ├── verify_meta_task.py            # Verifier script
    ├── evaluator.py                   # Evaluation logic
    └── task_answer_key.json           # Hidden answers (verifier-only)
```

This is a self-contained, runnable Harbor meta-task. Harbor uses only these files at runtime.
