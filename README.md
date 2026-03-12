# MedCLI

![Building MedCLI](cover.png)

An agentic system powered by frontier language models for solving complex, multi-step tasks over Electronic Health Record (EHR) databases through tool-augmented reasoning.

## Overview

MedCLI is a research project exploring how LLM-based agents (GPT, Claude) can serve as autonomous research assistants for clinical data analysis. The system equips models with a suite of callable tools — SQL execution, medical code lookup, statistical analysis, visualization, and more — enabling them to plan, query, compute, and reason over real EHR data to complete tasks that typically require significant domain expertise and manual effort.

## Harbor Background

This project uses Harbor as the terminal-task execution and evaluation substrate. Harbor provides a consistent trial lifecycle (agent run, verifier run, and artifacts), while MedCLI adds domain-specific EHR tasks, tools, and integrations.

Important pointers:

1. Harbor repo: https://github.com/harbor-framework/harbor
2. Harbor docs/wiki: https://deepwiki.com/harbor-framework/harbor
3. Pinned Harbor commit used here: https://github.com/harbor-framework/harbor/commit/c255479c1319f96f140b25e6ae0b86874ee05809
   - Maintenance note: periodically check for a newer stable Harbor release/commit.
   - Upgrade caution: Harbor upgrades can break custom agent integration interfaces (for example this repo's Codex wrapper at `src/medcli/agents/harbor/installed/codex.py`).
4. Local Harbor job configs in this repo: `jobs/example.yaml` (hello-world smoke test) and `jobs/medagentbench_meta.yaml` (single-task MedAgentBench meta-task).

## Tasks

The system targets 15 agentic EHR tasks spanning data understanding, clinical reasoning, and report generation:

| Task | Description |
|------|-------------|
| **Schema understanding** | Explore and document EHR database structure (tables, schemas, relationships) |
| **Factual QA** | Answer data-grounded clinical questions with SQL + reasoning |
| **Cross-schema ETL** | Map source EHR to target CDM (OMOP, FHIR, MEDS) with validation |
| **Cohort construction** | Assemble patient cohorts from natural-language inclusion/exclusion criteria |
| **Outcome prediction** | Retrieve features, find similar patients, produce risk estimates with evidence |
| **Trajectory summarization** | Generate longitudinal clinical summaries for a given patient |
| **Temporal reasoning** | Answer multi-hop temporal queries with time-window logic |
| **Treatment pathway analysis** | Extract and visualize common treatment sequences for a condition |
| **Trial eligibility** | Assess clinical trial eligibility for a patient with structured evidence |
| **Medication reconciliation** | Compile active medications and flag drug interactions |
| **Data quality auditing** | Detect inconsistencies, missing values, and implausible entries |
| **Report generation** | Draft clinical documents (referral letters, discharge summaries) from data |
| **Data aggregation** | Aggregate multiple EHR measurements into computed summaries or trends |
| **Clinical data recording** | Record new observations or updates into the clinical chart via structured APIs |
| **Care ordering** | Place orders/referrals/tests with appropriate coded payloads and rationale |

## Tools

The agent has access to tools across five categories:

- **Database & query** — SQL executor, schema inspector, query validator
- **Data analysis** — Python sandbox, statistical calculator, visualization generator
- **Medical knowledge** — ICD/CPT/LOINC lookup, RxNorm/DrugBank, guideline retriever, PubMed search
- **EHR utilities** — FHIR client, ClinicalTrials.gov search, de-identification checker
- **File & format** — CSV/Parquet reader, document parser, schema mapper, web fetcher, bash tools

## Task Suite Architecture

Tasks are first-class artifacts in this repository. Each task-type package can include:

- benchmark manifests under `sources/<benchmark_name>/`
- prompts, fixtures, and docs needed to reproduce the task

Task packages are organized by task type from the `Tasks` table above (for example `tasks/cohort_construction/`, `tasks/temporal_reasoning/`), not by benchmark source. If a new task type is added, update the `Tasks` section first, then add the corresponding `tasks/<task_type>/` package.

Shared orchestration still lives in `src/medcli/`, while `tasks/` owns task-type-specific assets and logic.

## Project Structure

```
MedCLI/
├── README.md
├── LICENSE
├── pyproject.toml
├── CLAUDE.md                         # Claude Code instructions
├── AGENTS.md                         # Codex agent instructions
├── PLANS.md                          # ExecPlan format definition
├── .claude/                          # Claude Code settings, commands, skills
├── .codex/                           # Codex-specific config
├── .agent/plans/                     # Individual ExecPlan files
├── src/medcli/
│   ├── agents/
│   │   ├── oai_agent/                # Core OpenAI-style agent package (core loop + parsing/policy/tool execution helpers)
│   │   └── harbor/installed/         # Harbor-installed agent wrappers (for example Codex adapter)
│   ├── tools/                        # Tool implementations
│   └── utils/                        # DB, sandbox, logging helpers
├── tasks/                            # Task suite: manifests + task-type assets
│   ├── selectors/                    # Reusable task selection manifests
│   ├── cohort_construction/          # Task-type package
│   │   └── sources/medagentbench/    # Benchmark manifests
│   ├── temporal_reasoning/           # Task-type package
│   │   └── sources/medagentbench/    # Benchmark manifests
│   └── report_generation/            # Task-type package
│       └── sources/                  # Optional benchmark manifests
├── run.py                            # Top-level benchmark runner CLI
├── demo.py                           # Interactive terminal demo CLI
├── scripts/                          # Setup/export/evaluation utilities organized by integration domain
│   └── medagentbench/                # MedAgentBench runtime, import, and evaluation scripts
├── results/                          # Run/evaluation artifacts (gitignored)
├── notebooks/                        # Analysis & paper figures
├── paper/                            # LaTeX source for arxiv submission
├── design/                           # Design docs, architecture, scope, ideas
└── tests/                            # Tool & agent tests
```

## Setup

```bash
# Clone the repo
git clone git@github.com:sheng-z/MedCLI.git
cd MedCLI

# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync --all-extras
```

Python version requirement: `>=3.12`.

## Harbor Usage

### Quick Start

Important: you must export `CODEX_AUTH_JSON` before running Harbor with Codex. Harbor runs the agent inside Docker, and without this variable Codex cannot authenticate in the container environment.

The MedAgentBench Harbor task generated in this repo is hardened for reproducibility:

- the FHIR sidecar image is pinned by digest
- the task environment does not require outbound internet
- the generated task tree is source-only; runtime files such as `submission.json` are created inside the running container, not committed under `harbor_tasks/`

```bash
# Export Codex auth for this shell session
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

# Run Harbor hello-world smoke test
uv run harbor run -c jobs/example.yaml

# Generate the single-task MedAgentBench Harbor task and run it
uv run python scripts/medagentbench/generate_harbor_tasks.py --input-root tasks --output-root harbor_tasks/medagentbench
uv run harbor run -c jobs/medagentbench_meta.yaml
```

Harbor writes run artifacts under `results/harbor/<timestamp>/`.

For step-by-step Harbor task debugging, use the reusable helpers under `debug/harbor/`. For the current MedAgentBench meta-task:

- `debug/harbor/medagentbench/smoke-meta-task.sh` covers the non-agent smoke path
- `debug/harbor/setup-agent.sh` is the generic default-agent setup step after `up-task-env.sh`
- `debug/harbor/medagentbench/run-manually.sh` is the task-specific one-command wrapper that uses that generic setup step internally and opens a ready-to-use shell

See [debug/README.md](/home/shezhan/repos/ehr-co-scientist/debug/README.md) for the full workflow.

## OAI Usage

### Demo

For an interactive demo, MedAgentBench is the recommended first run:

```bash
# Start local FHIR runtime
bash scripts/medagentbench/fhir_up.sh

# Launch demo
uv run python demo.py \
  --backend azure_openai \
  --model gpt-5-mini \
  --api-version 2025-03-01-preview \
  --fhir-base-url http://localhost:8080/fhir
```

The demo enables FHIR function-calling tools by default. Exit with `quit`, `exit`, or EOF (`Ctrl-D`).

When finished:

```bash
# Stop runtime
bash scripts/medagentbench/fhir_down.sh
```

For more MedAgentBench-specific demo details, see `scripts/medagentbench/README.md`.

### Run a Benchmark Evaluation

Benchmark workflows follow the same general pattern: prepare benchmark assets, import task manifests under `tasks/<task_type>/sources/<benchmark_name>/`, run `run.py`, and evaluate the results. MedAgentBench is one example:

```bash
# 1) Start local FHIR runtime (required before setup.sh sol backfill)
bash scripts/medagentbench/fhir_up.sh

# 2) Verify FHIR readiness
curl -sSf http://localhost:8080/fhir/metadata | head -c 200

# 3) Prepare benchmark assets
bash scripts/medagentbench/setup.sh

# 4) Import tasks into task-type manifests
uv run python scripts/medagentbench/import_tasks.py \
  --input data/medagentbench/test_data_v2.json \
  --funcs-json data/medagentbench/funcs_v1.json \
  --output-root tasks \
  --split std

# 5) Run a benchmark slice
uv run python run.py \
  --task medagentbench \
  --split std \
  --max-tasks 3 \
  --backend azure_openai \
  --model gpt-5-mini \
  --api-version 2025-03-01-preview \
  --fhir-base-url http://localhost:8080/fhir

# 6) Evaluate run outputs
uv run python scripts/medagentbench/evaluate.py \
  --task medagentbench \
  --results results/medagentbench/<run-id>/results.jsonl

# 7) Stop runtime
bash scripts/medagentbench/fhir_down.sh
```

Benchmark-specific imports (such as MedAgentBench) should map into the relevant task-type package under `tasks/<task_type>/sources/<benchmark_name>/`, rather than creating benchmark-named task roots.

Scripts should be grouped under `scripts/<integration_or_domain>/` as the repository grows (for example `scripts/medagentbench/`) to avoid an unscalable flat script list.

## MedAgentBench

For full MedAgentBench setup, execution, evaluation, and demo instructions, see `scripts/medagentbench/README.md`.

## License

TBD
