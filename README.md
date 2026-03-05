# EHR Co-Scientist

![Building an EHR Co-Scientist](cover.png)

An agentic system powered by frontier language models for solving complex, multi-step tasks over Electronic Health Record (EHR) databases through tool-augmented reasoning.

## Overview

EHR Co-Scientist is a research project exploring how LLM-based agents (GPT, Claude) can serve as autonomous research assistants for clinical data analysis. The system equips models with a suite of callable tools — SQL execution, medical code lookup, statistical analysis, visualization, and more — enabling them to plan, query, compute, and reason over real EHR data to complete tasks that typically require significant domain expertise and manual effort.

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

Tasks are first-class artifacts in this repository. Each task can include:

- declarative metadata (`task.yaml`)
- task-specific execution glue (`runner.py`)
- task-specific scoring logic (`evaluator.py`)
- prompts, fixtures, and docs needed to reproduce the task

Task packages are organized by task type from the `Tasks` table above (for example `tasks/cohort_construction/`, `tasks/temporal_reasoning/`), not by benchmark source. If a new task type is added, update the `Tasks` section first, then add the corresponding `tasks/<task_type>/` package.

Shared orchestration still lives in `src/ehr_co_scientist/`, while `tasks/` owns task-type-specific assets and logic.

## Project Structure

```
ehr-co-scientist/
├── README.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── CLAUDE.md                         # Claude Code instructions
├── AGENTS.md                         # Codex agent instructions
├── PLANS.md                          # ExecPlan format definition
├── .claude/                          # Claude Code settings, commands, skills
├── .codex/                           # Codex-specific config
├── .agent/plans/                     # Individual ExecPlan files
├── config/
│   └── agent.yaml                    # Model, tool whitelist, DB connection
├── src/ehr_co_scientist/
│   ├── agent.py                      # Core agent loop
│   ├── prompts/                      # System & task prompt templates
│   ├── tools/                        # Tool implementations
│   └── utils/                        # DB, sandbox, logging helpers
├── tasks/                            # Task suite: specs + runners + evaluators + fixtures
│   ├── registry.py                   # Task discovery/registration
│   ├── selectors/                    # Reusable task selection manifests
│   ├── cohort_construction/          # Task-type package
│   │   └── task.yaml                 # Task-type metadata/spec
│   ├── temporal_reasoning/           # Task-type package
│   │   └── task.yaml                 # Task-type metadata/spec
│   └── report_generation/            # Task-type package
│       └── task.yaml                 # Task-type metadata/spec
├── scripts/                          # Setup/export/evaluation utilities organized by integration domain
│   ├── setup_mimic.sh                # Core MIMIC bootstrap script
│   └── medagentbench/                # MedAgentBench runtime, import, and evaluation scripts
├── experiments/                      # Top-level run CLI, configs, and results
├── notebooks/                        # Analysis & paper figures
├── paper/                            # LaTeX source for arxiv submission
├── design/                           # Design docs, architecture, scope, ideas
└── tests/                            # Tool & agent tests
```

## Setup

```bash
# Clone the repo
git clone https://github.com/<user>/ehr-co-scientist.git
cd ehr-co-scientist

# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync --all-extras

# Copy and fill in API keys
cp .env.example .env

# Set up MIMIC database (requires PhysioNet credentials)
bash scripts/setup_mimic.sh
```

## Usage

```bash
# Run a task
python experiments/run.py --task medagentbench --split std --max-tasks 3 --model gpt-5.2

# Evaluate MedAgentBench results
python scripts/medagentbench/evaluate.py --task medagentbench --results experiments/results/medagentbench/<run-id>/results.jsonl
```

Task-local execution/scoring scripts live under each task-type package in `tasks/<task_type>/`. Benchmark-specific imports (such as MedAgentBench) should map into the relevant task-type package during integration work, rather than creating benchmark-named task roots.

Scripts should be grouped under `scripts/<integration_or_domain>/` as the repository grows (for example `scripts/medagentbench/`) to avoid an unscalable flat script list.

## MedAgentBench

For full MedAgentBench setup, execution, evaluation, and demo instructions, see `scripts/medagentbench/README.md`.

## License

TBD
