# MedCLI — Agent Instructions

> **Sync notice:** `AGENTS.md` and `CLAUDE.md` must always be identical.
> When you update one, update the other immediately.

## Project Overview

MedCLI is an agentic system powered by frontier language models for solving complex, multi-step tasks over Electronic Health Record (EHR) databases through tool-augmented reasoning. The system equips LLM-based agents with callable tools — SQL execution, medical code lookup, statistical analysis, visualization, and more — enabling them to plan, query, compute, and reason over real EHR data.

The repository is in a Harbor-first transition. New benchmark work should target Harbor task environments and Harbor jobs. The older OpenAI-style runner path remains temporarily for migration only.

## Repository Layout

- `src/medcli/agents/harbor/installed/` — Harbor installed-agent wrappers (for example Codex adapter).
- `src/medcli/agents/oai_agent/` — Legacy OpenAI-style agent package kept temporarily during migration.
- `src/medcli/tools/` — Shared tool implementations that are not Harbor-task-local helpers.
- `src/medcli/utils/` — Shared helpers for database access, sandboxed execution, and logging.
- `data/medagentbench/` — Canonical raw MedAgentBench benchmark assets.
- `data/ehrsql/` — EHRSQL benchmark JSON and SQLite databases.
- `harbor_tasks/medagentbench/` — Generated Harbor MedAgentBench meta-task.
- `harbor_tasks/ehrsql/` — Generated Harbor EHRSQL meta-task.
- `jobs/` — Harbor job configs.
- `debug/` — Harbor debug helpers and workflow docs.
- `scripts/medagentbench/` — Raw-data normalization, Harbor task generation, setup, and evaluation utilities.
- `scripts/ehrsql/` — EHRSQL setup, Harbor generation, and evaluation utilities.
- `tasks/` — Legacy task manifests grouped by task type; MedAgentBench entries here are transitional.
- `run.py` / `demo.py` — Legacy orchestration CLIs kept temporarily during migration.
- `results/` — Top-level run/evaluation artifacts directory (gitignored).
- `tests/` — Unit and integration tests.
- `.agent/plans/` — Individual ExecPlan files (see ExecPlans section below).

## Conventions

- **Python ≥ 3.12** is required. Use modern Python idioms (type hints, dataclasses, `match` statements where appropriate).
- **Packaging** is managed via `pyproject.toml`. Install with `uv sync --all-extras`. Add new dependencies with `uv add <package>`.
- **Environment variables** are loaded from `.env`. Never hard-code secrets.
- **Testing** uses `pytest`. Run the full suite with `pytest tests/` from the repo root.
- **Linting** uses `ruff`. Run `ruff check src/ tests/` before committing.
- **Formatting** uses `ruff format src/ tests/` before committing.
- **Docstrings** are required for public modules/functions and non-trivial internal helpers in `src/`; keep them concise and focused on purpose, inputs, and outputs.
- **Scripts layout** should avoid a flat `scripts/` list as integrations grow; place related scripts under subdirectories such as `scripts/medagentbench/`.
- **Commits** should be small, focused, and have descriptive messages. Prefer one logical change per commit.

## Harbor-First Rule

For MedAgentBench, the canonical source is `data/medagentbench/test_data_v2.json`, and the canonical runnable artifact is the Harbor meta-task under `harbor_tasks/medagentbench/`. Do not build new MedAgentBench features on top of `tasks/*.yaml`, `run.py`, `demo.py`, or `src/medcli/agents/oai_agent/` unless the work is explicitly about migration cleanup or removal.

## Tool Categories

When implementing or modifying shared MedCLI tools, respect the five-category taxonomy:

1. **Database & query** — SQL executor, schema inspector, query validator.
2. **Data analysis** — Python sandbox, statistical calculator, visualization generator.
3. **Medical knowledge** — ICD/CPT/LOINC lookup, RxNorm/DrugBank, guideline retriever, PubMed search.
4. **EHR utilities** — FHIR client, ClinicalTrials.gov search, de-identification checker.
5. **File & format** — CSV/Parquet reader, document parser, schema mapper, web fetcher, bash tools.

Each shared tool lives in its own module under `src/medcli/tools/`. MedAgentBench-specific primitive helpers that belong to the Harbor task environment should live in generated Harbor workspace scripts rather than in the legacy OpenAI-style tool registry.

## Tasks

The system supports 15 agentic EHR task types. The `tasks/<task_type>/` tree still exists for legacy manifests and migration support. For MedAgentBench, however, the canonical task-generation path is now raw JSON to Harbor meta-task generation, not YAML manifests. If new task types are introduced in repository-level documentation, update the `Tasks` section in `README.md`.

## ExecPlans

When writing complex features or significant refactors, use an ExecPlan (as described in `PLANS.md`) from design to implementation. ExecPlan files are stored in `.agent/plans/` and must follow the format, requirements, and skeleton defined in `PLANS.md` to the letter. Read that file in full before authoring or implementing any ExecPlan.

Key rules (see `PLANS.md` for the complete specification):

- Every ExecPlan must be **fully self-contained** — a novice with no prior context can implement it end-to-end.
- Every ExecPlan is a **living document** — update it as progress is made, decisions are taken, and surprises are discovered.
- Every ExecPlan must contain and maintain these sections: `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective`.
- Anchor plans with **observable outcomes** — commands to run, outputs to expect, behavior a human can verify.
- Resolve ambiguities in the plan itself; do not defer decisions to the implementer.
- When implementing an ExecPlan, proceed through milestones autonomously — do not prompt for "next steps".
- Commit frequently and keep the Progress section current at every stopping point.

## Running the Project

```bash
# Install dependencies
uv sync --all-extras

# Activate virtual environment
source .venv/bin/activate
```

### Harbor Usage

Important: you must export `CODEX_AUTH_JSON` before running Harbor with Codex. Harbor runs the agent inside Docker, and without this variable Codex cannot authenticate in the container environment.

The MedAgentBench Harbor task is a single meta-task at `harbor_tasks/medagentbench/`. It is generated directly from `data/medagentbench/test_data_v2.json`, bundles the current 10-case slice (`task1_1` through `task10_1`), runs against a local FHIR sidecar, and evaluates a `submission.json` file whose public rows contain only safe task text plus `final_answer` and `payload`. Hidden answer keys and reference write payloads live only under `tests/` in the generated Harbor task.

EHRSQL is a text-to-SQL benchmark on MIMIC-III and eICU databases. The EHRSQL Harbor task is generated from raw JSON at `data/ehrsql/` and provides all validation set tasks (~2,239 tasks) or custom selections.

```bash
# Export Codex auth for this shell session
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

# Run Harbor hello-world smoke test
uv run harbor run -c jobs/example.yaml

# Generate and run MedAgentBench Harbor task
uv run python scripts/medagentbench/generate_harbor_tasks.py \
  --input-json data/medagentbench/test_data_v2.json \
  --output-root harbor_tasks/medagentbench
uv run harbor run -c jobs/medagentbench_meta.yaml

# Generate and run EHRSQL Harbor task (validation set)
uv run python scripts/ehrsql/setup.sh                    # Download JSON task definitions
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --valid-json data/ehrsql/mimic_iii/valid.json data/ehrsql/eicu/valid.json \
  --output-root harbor_tasks/ehrsql
uv run harbor run -c jobs/ehrsql_meta.yaml
```

For step-by-step Harbor task debugging, use the helpers under `debug/harbor/`:

- `debug/harbor/medagentbench/smoke-meta-task.sh` covers the non-agent smoke path.
- `debug/harbor/setup-agent.sh` is the generic default-agent setup step after `up-task-env.sh`.
- `debug/harbor/medagentbench/run-manually.sh` is the task-specific wrapper that performs setup and opens a ready-to-use Codex shell.
- `debug/README.md` documents the full manual build, bring-up, agent-setup, verifier, and cleanup workflow.

### Legacy OAI Path

The older OpenAI-style runner path is transitional and frozen.

```bash
# Transitional MedAgentBench import path
uv run python scripts/medagentbench/import_tasks.py \
  --input data/medagentbench/test_data_v2.json \
  --funcs-json data/medagentbench/funcs_v1.json \
  --output-root tasks \
  --split std

# Transitional runner path
uv run python run.py --task medagentbench --split std --max-tasks 3
```

Do not build new MedAgentBench features on that path.

## EHRSQL

EHRSQL is a Harbor-first integration with no legacy OpenAI-style artifacts. For setup, task generation, and customization details, see `scripts/ehrsql/README.md`. The canonical sources are:
- **Raw task JSON**: Downloaded from https://github.com/glee4810/EHRSQL (valid.json, test.json, tables.json)
- **SQLite databases**: Downloaded separately from Google Drive (see `scripts/ehrsql/README.md`)
- **Generated Harbor task**: `harbor_tasks/ehrsql/` (configurable selection of validation or test split tasks)
