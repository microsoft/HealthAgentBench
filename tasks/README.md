# Tasks

This directory contains generated Harbor task environments for benchmark integrations.

Current benchmark tasks in this repo:

| Benchmark | Task Directory | Description | Notes |
|-----------|----------------|-------------|-------|
| **MedAgentBench** | `medagentbench/` | Interactive EHR benchmark focused on multi-step retrieval, reasoning, and structured action tasks over clinical data. | Harbor-generated benchmark task built from raw benchmark assets under `scripts/medagentbench/`. |
| **EHRSQL_Lite** | `ehrsql/` | Text-to-SQL benchmark over EHR databases (MIMIC-III, eICU). We use a lite version that covers 250 samples from MIMIC-III and 250 samples from eicu. Agent generates SQL queries or identifies unanswerable questions. |THE harbor task directories are generated using `scripts/ehrsql/generate_harbor_tasks.py`.|
| **MIMIC-IV MEDS Extraction ETL** | `mimic_iv_meds/` | ETL benchmark for converting the open MIMIC-IV demo dataset into MEDS by following the pinned upstream `MIMIC_IV_MEDS` repo. | Adapted Harbor task with staged demo input, agent-run `uv` setup, and directory-output verification against a gold summary. |

For the canonical repo-level workflow for integrating a new benchmark, see `design/benchmark_addition_workflow.md`.

For benchmark-specific task generation details, see `scripts/<benchmark>/README.md`.



# MedCLI Benchmark Results

| Task | Split | Model | Score |
|------|-------|-------|-------|
| ehrsql | mimic_iii_test | gpt-5.3-codex | 42.69 |
| ehrsql | eicu_test | gpt-5.3-codex | 39.3 |


## Metric Definitions

For EHRSQL, **Score** refers to Execution F1 — the harmonic mean of execution precision and execution recall. Execution precision is the fraction of agent-predicted answerable queries whose results match the gold SQL results exactly. Execution recall is the fraction of gold answerable queries that the agent answered correctly. Both metrics use set-based comparison of query results against the SQLite database, which is more robust than string-based SQL matching.