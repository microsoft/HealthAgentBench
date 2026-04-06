# MedCLI — Agent Instructions

> **Sync notice:** `AGENTS.md` and `CLAUDE.md` must always be identical.
> When you update one, update the other immediately.

## Project Overview

MedCLI is a Harbor-first research project for health tasks. The core environment is a terminal: a generic interface through which agents can inspect data, use tools, access medical resources, take actions, and iteratively understand, reason about, and solve tasks across many kinds of medical data and systems.

The repository currently uses Harbor task environments and Harbor jobs as the supported execution path for benchmark work.

## Repository Layout

- `src/medcli/agents/harbor/installed/` — Harbor installed-agent wrappers (for example Codex adapter).
- `tasks/<benchmark>/` — Generated Harbor benchmark task.
- `jobs/` — Harbor job configs.
- `debug/` — Harbor debug helpers and workflow docs.
- `scripts/<benchmark>/` — Benchmark-specific setup, normalization, task generation, and evaluation utilities.
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
- **Scripts layout** should avoid a flat `scripts/` list as integrations grow; place related scripts under subdirectories such as `scripts/<benchmark>/`.
- **Commits** should be small, focused, and have descriptive messages. Prefer one logical change per commit.

## Harbor-First Rule

For a benchmark integrated through Harbor, the canonical source should live under `scripts/<benchmark>/assets/`, and the canonical runnable artifact should live under `tasks/<benchmark>/`. Do not reintroduce alternate benchmark execution paths outside Harbor.

## Tasks

The system supports 15 agentic health task types conceptually. For benchmark integrations, prefer raw source assets to Harbor task generation rather than parallel runner stacks.

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

## Usage

Important: Harbor Codex runs expect a local Codex login on the host so `~/.codex/auth.json` is available. You can override the default path with `CODEX_AUTH_FILE`.

```bash
# Verify local Codex login state
codex login status

uv run harbor run -c jobs/<benchmark>.yaml
```

## Current Benchmark

The current benchmark in this repo is `medagentbench`.

- Task: `tasks/medagentbench/`
- Scripts: `scripts/medagentbench/`
- Job: `jobs/medagentbench_meta.yaml`
- Debug: `debug/medagentbench/README.md`

## Task Creation

For the canonical repo-level workflow for adding a new benchmark, see `design/benchmark_addition_workflow.md`.

For benchmark-specific task creation details, see `scripts/<benchmark>/README.md`.

For the current MedAgentBench benchmark, see `scripts/medagentbench/README.md`.

## Debug

For generic Harbor debug workflow details, see `debug/README.md`.

For benchmark-specific debug workflow details, see `debug/<benchmark>/README.md`.

For the current MedAgentBench benchmark, see `debug/medagentbench/README.md`.
