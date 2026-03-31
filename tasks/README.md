# Tasks

This directory contains generated Harbor task environments for benchmark integrations.

Current benchmark tasks in this repo:

| Benchmark | Task Directory | Description | Notes |
|-----------|----------------|-------------|-------|
| **MedAgentBench** | `medagentbench/` | Interactive EHR benchmark focused on multi-step retrieval, reasoning, and structured action tasks over clinical data. | Harbor-generated benchmark task built from raw benchmark assets under `scripts/medagentbench/`. |
| **EHRSQL** | `ehrsql/` | Text-to-SQL benchmark over EHR databases (MIMIC-III, eICU). Agent generates SQL queries or identifies unanswerable questions. | Splits: `mimic_iii_valid`, `mimic_iii_test`, `eicu_valid`, `eicu_test`. Per-worker task splits generated via `scripts/ehrsql/generate_harbor_tasks.py`. |

For benchmark-specific task generation details, see `scripts/<benchmark>/README.md`.



# MedCLI Benchmark Results

| Task | Split | Model | Score |
|------|-------|-------|-------|
| ehrsql | mimic_iii_test | gpt-5.3-codex |  |
| ehrsql | eicu_test | gpt-5.3-codex | 36.63 |


## Metric Definitions

For EHRSQL, **Score** refers to Execution F1 — the harmonic mean of execution precision and execution recall. Execution precision is the fraction of agent-predicted answerable queries whose results match the gold SQL results exactly. Execution recall is the fraction of gold answerable queries that the agent answered correctly. Both metrics use set-based comparison of query results against the SQLite database, which is more robust than string-based SQL matching.