# EHR Co-Scientist — Agent Instructions

> **Sync notice:** This file (`AGENTS.md`) and `CLAUDE.md` must always be identical.
> When you update one, update the other immediately.

## Project Overview

EHR Co-Scientist is an agentic system powered by frontier language models for solving complex, multi-step tasks over Electronic Health Record (EHR) databases through tool-augmented reasoning. The system equips LLM-based agents with callable tools — SQL execution, medical code lookup, statistical analysis, visualization, and more — enabling them to plan, query, compute, and reason over real EHR data.

## Repository Layout

- `config/agent.yaml` — Model selection, tool whitelist, database connection settings.
- `src/ehr_co_scientist/agent.py` — Core agent loop.
- `src/ehr_co_scientist/prompts/` — System and task prompt templates.
- `src/ehr_co_scientist/tools/` — Tool implementations (DB, analysis, medical knowledge, EHR utilities, file/format).
- `src/ehr_co_scientist/utils/` — Shared helpers for database access, sandboxed execution, and logging.
- `tasks/` — Task definitions in YAML, one per task type.
- `benchmarks/` — Evaluation protocol, datasets, and gold-standard answers.
- `experiments/` — Run configurations, CLI entry points, and result artifacts.
- `notebooks/` — Jupyter notebooks for analysis and paper figures.
- `paper/` — LaTeX source for the arxiv submission.
- `scripts/` — Setup and export utilities (e.g., `setup_mimic.sh`).
- `tests/` — Unit and integration tests for tools and the agent.
- `.agent/plans/` — Individual ExecPlan files (see ExecPlans section below).

## Conventions

- **Python ≥ 3.11** is required. Use modern Python idioms (type hints, dataclasses, `match` statements where appropriate).
- **Packaging** is managed via `pyproject.toml`. Install with `uv sync --all-extras`. Add new dependencies with `uv add <package>`.
- **Environment variables** are loaded from `.env` (see `.env.example` for required keys). Never hard-code secrets.
- **SQL** targets PostgreSQL (MIMIC-IV). Always use parameterized queries; never interpolate user input.
- **Testing** uses `pytest`. Run the full suite with `pytest tests/` from the repo root.
- **Linting** uses `ruff`. Run `ruff check src/ tests/` before committing.
- **Formatting** uses `ruff format`. Run `ruff format src/ tests/` before committing.
- **Commits** should be small, focused, and have descriptive messages. Prefer one logical change per commit.

## Tool Categories

When implementing or modifying tools, respect the five-category taxonomy:

1. **Database & query** — SQL executor, schema inspector, query validator.
2. **Data analysis** — Python sandbox, statistical calculator, visualization generator.
3. **Medical knowledge** — ICD/CPT/LOINC lookup, RxNorm/DrugBank, guideline retriever, PubMed search.
4. **EHR utilities** — FHIR client, ClinicalTrials.gov search, de-identification checker.
5. **File & format** — CSV/Parquet reader, document parser, schema mapper, web fetcher, bash tools.

Each tool lives in its own module under `src/ehr_co_scientist/tools/` and must expose a consistent interface that the agent loop in `agent.py` can discover and invoke.

## Tasks

The system supports 12 agentic EHR tasks. Task definitions live in `tasks/` as YAML files. When adding or modifying tasks, ensure the YAML schema stays consistent and that evaluation scripts in `benchmarks/` can consume the output.

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

# Copy and fill in API keys
cp .env.example .env

# Set up MIMIC database (requires PhysioNet credentials)
bash scripts/setup_mimic.sh

# Run a task
python experiments/run.py --task cohort_construction --model claude-4-sonnet

# Evaluate results
python benchmarks/evaluate.py --task cohort_construction --results experiments/results/

# Run tests
pytest tests/

# Lint and format
ruff check src/ tests/
ruff format src/ tests/
```
