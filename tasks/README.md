# Tasks

This directory contains generated Harbor task environments for benchmark integrations.

Current benchmark tasks in this repo:

| Benchmark | Task Directory | Description | Notes |
|-----------|----------------|-------------|-------|
| **MedAgentBench** | `medagentbench/` | Interactive EHR benchmark focused on multi-step retrieval, reasoning, and structured action tasks over clinical data. | Harbor-generated benchmark task built from raw benchmark assets under `scripts/medagentbench/`. |

For the canonical repo-level workflow for integrating a new benchmark, see `design/benchmark_addition_workflow.md`.

For benchmark-specific task generation details, see `scripts/<benchmark>/README.md`.
