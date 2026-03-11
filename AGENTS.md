# EHR Co-Scientist — Agent Instructions

> **Sync notice:** `AGENTS.md` and `CLAUDE.md` must always be identical.
> When you update one, update the other immediately.

## Project Overview

EHR Co-Scientist is an agentic system powered by frontier language models for solving complex, multi-step tasks over Electronic Health Record (EHR) databases through tool-augmented reasoning. The system equips LLM-based agents with callable tools — SQL execution, medical code lookup, statistical analysis, visualization, and more — enabling them to plan, query, compute, and reason over real EHR data.

## Repository Layout

- `src/ehr_co_scientist/agents/oai_agent/` — Core OpenAI-style agent package (`core.py`, parsing/policy/tool-exec modules).
- `src/ehr_co_scientist/agents/harbor/installed/` — Harbor installed-agent wrappers (for example Codex adapter).
- `src/ehr_co_scientist/tools/` — Tool implementations (DB, analysis, medical knowledge, EHR utilities, file/format).
- `src/ehr_co_scientist/utils/` — Shared helpers for database access, sandboxed execution, and logging.
- `tasks/` — Task suite package organized by task type (benchmark manifests, prompts, fixtures, selectors, and task-local docs).
- `scripts/medagentbench/` — MedAgentBench runtime orchestration, import, and evaluation utilities.
- `run.py` / `demo.py` — Top-level orchestration CLIs for benchmark runs and interactive demos.
- `results/` — Top-level run/evaluation artifacts directory (gitignored).
- `notebooks/` — Jupyter notebooks for analysis and paper figures.
- `paper/` — LaTeX source for the arxiv submission.
- `scripts/` — Setup and export utilities organized by integration/domain (e.g., `medagentbench/`).
- `tests/` — Unit and integration tests for tools and the agent.
- `.agent/plans/` — Individual ExecPlan files (see ExecPlans section below).

## Conventions

- **Python ≥ 3.12** is required. Use modern Python idioms (type hints, dataclasses, `match` statements where appropriate).
- **Packaging** is managed via `pyproject.toml`. Install with `uv sync --all-extras`. Add new dependencies with `uv add <package>`.
- **Environment variables** are loaded from `.env`. Never hard-code secrets.
- **SQL** targets PostgreSQL (MIMIC-IV). Always use parameterized queries; never interpolate user input.
- **Testing** uses `pytest`. Run the full suite with `pytest tests/` from the repo root.
- **Linting** uses `ruff`. Run `ruff check src/ tests/` before committing.
- **Formatting** uses `ruff format`. Run `ruff format src/ tests/` before committing.
- **Docstrings** are required for public modules/functions and non-trivial internal helpers in `src/`; keep them concise and focused on purpose/inputs/outputs.
- **Scripts layout** should avoid a flat `scripts/` list as integrations grow; place related scripts under subdirectories such as `scripts/medagentbench/`.
- **Commits** should be small, focused, and have descriptive messages. Prefer one logical change per commit.

## Tool Categories

When implementing or modifying tools, respect the five-category taxonomy:

1. **Database & query** — SQL executor, schema inspector, query validator.
2. **Data analysis** — Python sandbox, statistical calculator, visualization generator.
3. **Medical knowledge** — ICD/CPT/LOINC lookup, RxNorm/DrugBank, guideline retriever, PubMed search.
4. **EHR utilities** — FHIR client, ClinicalTrials.gov search, de-identification checker.
5. **File & format** — CSV/Parquet reader, document parser, schema mapper, web fetcher, bash tools.

Each tool lives in its own module under `src/ehr_co_scientist/tools/` and must expose a consistent interface that the agent loop in `src/ehr_co_scientist/agents/oai_agent/core.py` can discover and invoke.

## Tasks

The system supports 15 agentic EHR task types. Treat each task type as a first-class package under `tasks/<task_type>/` with benchmark manifests under `sources/<benchmark_name>/` plus optional prompts, fixtures, and task-local docs. Organize by task type from `README.md` (for example `cohort_construction`, `temporal_reasoning`), not by benchmark source name. If new task types are introduced, update the `Tasks` section in `README.md` and add matching packages. Keep shared orchestration/runtime logic in `src/ehr_co_scientist/`, and keep top-level CLIs in `run.py`/`demo.py` plus integration-specific scripts (for example `scripts/medagentbench/evaluate.py`) responsible for consistent execution.

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

Important: export `CODEX_AUTH_JSON` before running Harbor with Codex. Harbor runs inside Docker, and without this variable Codex cannot authenticate in the container environment.

```bash
# Harbor quick start
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run harbor run -c jobs/example.yaml
```

### OAI Usage

```bash
# Demo workflow (MedAgentBench recommended first run)
bash scripts/medagentbench/fhir_up.sh
uv run python demo.py \
  --backend azure_openai \
  --model gpt-5-mini \
  --api-version 2025-03-01-preview \
  --fhir-base-url http://localhost:8080/fhir
bash scripts/medagentbench/fhir_down.sh

# Benchmark evaluation workflow (MedAgentBench example)
bash scripts/medagentbench/fhir_up.sh
curl -sSf http://localhost:8080/fhir/metadata | head -c 200
bash scripts/medagentbench/setup.sh
uv run python scripts/medagentbench/import_tasks.py \
  --input data/medagentbench/test_data_v2.json \
  --funcs-json data/medagentbench/funcs_v1.json \
  --output-root tasks \
  --split std
uv run python run.py \
  --task medagentbench \
  --split std \
  --max-tasks 3 \
  --backend azure_openai \
  --model gpt-5-mini \
  --api-version 2025-03-01-preview \
  --fhir-base-url http://localhost:8080/fhir
uv run python scripts/medagentbench/evaluate.py \
  --task medagentbench \
  --results results/medagentbench/<run-id>/results.jsonl
bash scripts/medagentbench/fhir_down.sh

# Run tests
pytest tests/

# Lint and format
ruff check src/ tests/
ruff format src/ tests/
```
