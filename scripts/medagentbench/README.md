# MedAgentBench Scripts and Runtime

This directory contains the Harbor-first MedAgentBench utilities.

## Canonical Source and Canonical Runner

- Canonical source benchmark file: `scripts/medagentbench/assets/test_data_v2.json`
- Canonical Harbor task generator: `scripts/medagentbench/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/medagentbench/`
- Canonical Harbor evaluator: `scripts/medagentbench/harbor_evaluator.py`
- Hidden Harbor answer key location after generation: `tasks/medagentbench/tests/`

## Files in This Directory

- `setup.sh`: idempotent asset bootstrap, schema validation, and `sol` backfill for `scripts/medagentbench/assets/`
- `generate_harbor_tasks.py`: generates the single Harbor MedAgentBench meta-task directly from raw JSON
- `harbor_evaluator.py`: Harbor-specific evaluator for the Harbor submission schema
- `normalization.py`: shared raw-task normalization helpers reused by Harbor generation

The MedAgentBench-compatible FHIR sidecar is now provided through the generated Harbor task environment and the debug workflow under `debug/`.

## Quick Start

The `run_and_evaluate.sh` script handles data download, task generation, and Harbor execution in one command:

```bash
bash scripts/medagentbench/run_and_evaluate.sh jobs/medagentbench_meta.yaml
bash scripts/medagentbench/run_and_evaluate.sh jobs/medagentbench_meta.yaml -m gpt-5.1-codex-mini --ak reasoning_effort=low
```

Or via the top-level entry point:

```bash
bash medcli_evaluate.sh --task medagentbench --config jobs/medagentbench_meta.yaml
```

## Manual Workflow

```bash
# 1) Prepare benchmark assets
bash scripts/medagentbench/setup.sh

# 2) Generate the Harbor task directly from raw benchmark JSON
uv run python scripts/medagentbench/generate_harbor_tasks.py \
  --input-json scripts/medagentbench/assets/test_data_v2.json \
  --output-root tasks/medagentbench

# 3) Set up auth (choose one)
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
# or
export AZURE_OPENAI_API_KEY="<key>"
export CODEX_TASK_TOML="$(cat ~/.codex/config.toml)"

# 4) Run the Harbor meta-task
uv run harbor run -c jobs/medagentbench_meta.yaml
```
