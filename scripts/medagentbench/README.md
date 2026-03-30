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

## Canonical Harbor Workflow

```bash
# 1) Prepare benchmark assets
bash scripts/medagentbench/setup.sh

# 2) Generate the Harbor task directly from raw benchmark JSON
uv run python scripts/medagentbench/generate_harbor_tasks.py \
  --input-json scripts/medagentbench/assets/test_data_v2.json \
  --output-root tasks/medagentbench

# 3) Verify Codex auth is available on the host
codex login status

# 4) Run the Harbor meta-task
uv run harbor run -c jobs/medagentbench_meta.yaml
```
