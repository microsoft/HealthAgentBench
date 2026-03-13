# MedCLI

![Building MedCLI](cover.png)

An agentic system powered by frontier language models for solving complex, multi-step tasks over Electronic Health Record (EHR) databases through tool-augmented reasoning.

## Overview

MedCLI is a research project exploring how LLM-based agents can serve as autonomous research assistants for clinical data analysis. The repository is currently in a Harbor-first transition: new benchmark tasks and agent runs are expected to live in Harbor task environments, while the older OpenAI-style runner path remains in the tree only as a temporary migration layer.

## Harbor Background

This project uses Harbor as the terminal-task execution and evaluation substrate. Harbor provides a consistent trial lifecycle (agent run, verifier run, and artifacts), while MedCLI adds domain-specific EHR tasks, Harbor task environments, and benchmark integrations.

Important pointers:

1. Harbor repo: https://github.com/harbor-framework/harbor
2. Harbor docs/wiki: https://deepwiki.com/harbor-framework/harbor
3. Pinned Harbor commit used here: https://github.com/harbor-framework/harbor/commit/c255479c1319f96f140b25e6ae0b86874ee05809
   - Maintenance note: periodically check for a newer stable Harbor release or commit.
   - Upgrade caution: Harbor upgrades can break custom agent integration interfaces such as `src/medcli/agents/harbor/installed/codex.py`.
4. Local Harbor job configs in this repo: `jobs/example.yaml` (hello-world smoke test) and `jobs/medagentbench_meta.yaml` (single-task MedAgentBench meta-task).

## Tasks

The system targets 15 agentic EHR task types spanning data understanding, clinical reasoning, and report generation:

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

## Task Sources

For MedAgentBench specifically, the canonical source is now the original raw benchmark JSON in `data/medagentbench/test_data_v2.json`. The older YAML manifests under `tasks/*/sources/medagentbench/` are transitional compatibility artifacts produced by `scripts/medagentbench/import_tasks.py`; they are frozen and will be removed after the Harbor migration is complete.

## Project Structure

```text
MedCLI/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── PLANS.md
├── .agent/plans/                     # ExecPlans, including Harbor migration plans
├── data/medagentbench/               # Canonical raw MedAgentBench benchmark assets
├── harbor_tasks/medagentbench/       # Generated Harbor meta-task for the current MedAgentBench slice
├── jobs/                             # Harbor job configs
├── debug/                            # Harbor-oriented debug helpers and workflow docs
├── src/medcli/
│   ├── agents/harbor/installed/      # Harbor installed-agent wrappers
│   ├── agents/oai_agent/             # Legacy OpenAI-style agent stack (frozen during migration)
│   ├── tools/                        # Shared MedCLI tools used outside Harbor task-local helpers
│   └── utils/
├── scripts/medagentbench/            # Raw-data import, Harbor generation, setup, and evaluation helpers
├── tasks/                            # Legacy task manifests grouped by task type (transition-only for MedAgentBench)
├── run.py                            # Legacy benchmark runner CLI (transition-only)
├── demo.py                           # Legacy demo CLI (transition-only)
├── results/                          # Run and evaluation artifacts (gitignored)
└── tests/
```

## Setup

```bash
# Clone the repo
git clone git@github.com:sheng-z/MedCLI.git
cd MedCLI

# Install dependencies
uv sync --all-extras
```

Python version requirement: `>=3.12`.

## Harbor Usage

### Quick Start

Important: export `CODEX_AUTH_JSON` before running Harbor with Codex. Harbor runs the agent inside Docker, and without this variable Codex cannot authenticate in the container environment.

The MedAgentBench Harbor task generated in this repo is a single meta-task at `harbor_tasks/medagentbench/`. It is generated directly from `data/medagentbench/test_data_v2.json`, uses a local FHIR sidecar, exposes MedAgentBench primitive helpers inside the task workspace, and evaluates a `submission.json` file whose public rows contain only safe task text plus `final_answer` and `payload`. Hidden answer keys and reference write payloads live only under `tests/` in the generated Harbor task.

```bash
# Export Codex auth for this shell session
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

# Run Harbor hello-world smoke test
uv run harbor run -c jobs/example.yaml

# Generate the MedAgentBench Harbor meta-task from raw JSON and run it
uv run python scripts/medagentbench/generate_harbor_tasks.py \
  --input-json data/medagentbench/test_data_v2.json \
  --output-root harbor_tasks/medagentbench
uv run harbor run -c jobs/medagentbench_meta.yaml
```

Harbor writes run artifacts under `results/harbor/<timestamp>/`.

For step-by-step Harbor task debugging, use the helpers under `debug/harbor/`.

- `debug/harbor/medagentbench/smoke-meta-task.sh` covers the non-agent smoke path.
- `debug/harbor/setup-agent.sh` is the generic default-agent setup step after `up-task-env.sh`.
- `debug/harbor/medagentbench/run-manually.sh` performs agent setup and opens a ready-to-use Codex shell for the MedAgentBench Harbor task.
- `debug/README.md` documents the full manual build, bring-up, agent-setup, verifier, and cleanup workflow.

## Legacy OAI Path

The older OpenAI-style runner path remains in the repository temporarily so migration can happen incrementally, but it is no longer the canonical MedAgentBench workflow.

- `tasks/*/sources/medagentbench/*.yaml` is transitional.
- `run.py` and `demo.py` are transitional.
- `src/medcli/agents/oai_agent/` is transitional.
- `scripts/medagentbench/import_tasks.py` and `scripts/medagentbench/evaluator.py` remain only to support that temporary path.

No new MedAgentBench work should be built on top of that path.

## MedAgentBench

For Harbor-oriented MedAgentBench setup and task-generation details, see `scripts/medagentbench/README.md` and `debug/README.md`.

## License

TBD
