# Tasks

This directory contains generated Harbor task environments for benchmark integrations.

Current benchmark tasks in this repo:

| Benchmark | Task Directory | Description | Notes |
|-----------|----------------|-------------|-------|
| **MedAgentBench** | `medagentbench/` | Interactive EHR benchmark focused on multi-step retrieval, reasoning, and structured action tasks over clinical data. | Harbor-generated benchmark task built from raw benchmark assets under `scripts/medagentbench/`. |
| **MIMIC-IV MEDS Extraction ETL** | `mimic_iv_meds/` | ETL benchmark for converting the open MIMIC-IV demo dataset into MEDS by following the pinned upstream `MIMIC_IV_MEDS` repo. | Adapted Harbor task with staged demo input, agent-run `uv` setup, and directory-output verification against a gold summary. |

For the canonical repo-level workflow for integrating a new benchmark, see `design/benchmark_addition_workflow.md`.

For benchmark-specific task generation details, see `scripts/<benchmark>/README.md`.
