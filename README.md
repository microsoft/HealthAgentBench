# EHR Co-Scientist

![Building an EHR Co-Scientist](cover.png)

An agentic system powered by frontier language models for solving complex, multi-step tasks over Electronic Health Record (EHR) databases through tool-augmented reasoning.

## Overview

EHR Co-Scientist is a research project exploring how LLM-based agents (GPT, Claude) can serve as autonomous research assistants for clinical data analysis. The system equips models with a suite of callable tools — SQL execution, medical code lookup, statistical analysis, visualization, and more — enabling them to plan, query, compute, and reason over real EHR data to complete tasks that typically require significant domain expertise and manual effort.

## Tasks

The system targets 12 agentic EHR tasks spanning data understanding, clinical reasoning, and report generation:

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

## Tools

The agent has access to tools across five categories:

- **Database & query** — SQL executor, schema inspector, query validator
- **Data analysis** — Python sandbox, statistical calculator, visualization generator
- **Medical knowledge** — ICD/CPT/LOINC lookup, RxNorm/DrugBank, guideline retriever, PubMed search
- **EHR utilities** — FHIR client, ClinicalTrials.gov search, de-identification checker
- **File & format** — CSV/Parquet reader, document parser, schema mapper, web fetcher, bash tools

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
├── tasks/                            # Task definitions (YAML)
├── benchmarks/                       # Evaluation protocol, datasets, gold answers
├── experiments/                      # Run configs, CLI, results
├── notebooks/                        # Analysis & paper figures
├── paper/                            # LaTeX source for arxiv submission
├── design/                           # Design docs, architecture, scope, ideas
├── scripts/                          # Setup & export utilities
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
python experiments/run.py --task cohort_construction --model claude-4-sonnet

# Evaluate results
python benchmarks/evaluate.py --task cohort_construction --results experiments/results/
```

## License

TBD
