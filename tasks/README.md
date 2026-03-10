# Tasks

This directory contains first-class task-type packages.

Packages are organized by task type defined in `README.md` (for example `cohort_construction`, `temporal_reasoning`), not by benchmark/source name.

Each task-type package under `tasks/<task_type>/` can include:

- `sources/<benchmark_name>/`: benchmark manifests grouped by source and split
- `prompt.md`: task-specific prompt and protocol notes
- `fixtures/`: task-local sample inputs/outputs
- `README.md`: implementation notes and usage

Benchmark integrations (for example MedAgentBench) should be mapped into the relevant task-type package at integration time, usually under a `sources/<benchmark_name>/` subdirectory.

Shared orchestration belongs in `src/ehr_co_scientist/`. Top-level run/evaluate CLIs in `run.py`/`demo.py` and integration-specific script packages (for example `scripts/medagentbench/`) should load benchmark manifests directly from the relevant task-type packages.
