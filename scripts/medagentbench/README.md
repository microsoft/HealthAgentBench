# MedAgentBench Scripts and Runtime

This directory contains the MedAgentBench migration utilities. The canonical MedAgentBench path in this repository is now Harbor-first and raw-JSON-first.

## Canonical Source and Canonical Runner

- Canonical source benchmark file: `data/medagentbench/test_data_v2.json`
- Canonical Harbor task generator: `scripts/medagentbench/generate_harbor_tasks.py`
- Canonical runnable task artifact: `harbor_tasks/medagentbench/`
- Canonical Harbor evaluator: `scripts/medagentbench/harbor_evaluator.py`
- Hidden Harbor answer key location after generation: `harbor_tasks/medagentbench/tests/`

The older YAML manifest importer and legacy evaluator remain in this directory temporarily for migration support only.

## Files in This Directory

- `setup.sh`: idempotent asset bootstrap, schema validation, and `sol` backfill for `data/medagentbench/`
- `fhir_up.sh`: starts the local MedAgentBench-compatible FHIR runtime
- `fhir_down.sh`: stops the local FHIR runtime
- `generate_harbor_tasks.py`: generates the single Harbor MedAgentBench meta-task directly from raw JSON
- `harbor_evaluator.py`: Harbor-specific evaluator for the Harbor submission schema
- `normalization.py`: shared raw-task normalization helpers reused by Harbor generation and the legacy importer
- `import_tasks.py`: legacy YAML importer retained temporarily during migration
- `evaluator.py`: legacy evaluator retained temporarily during migration
- `docker-compose.yaml`: Docker Compose runtime definition for the local MedAgentBench-compatible FHIR server

## Canonical Harbor Workflow

```bash
# 1) Prepare benchmark assets
bash scripts/medagentbench/setup.sh

# 2) Generate the Harbor task directly from raw benchmark JSON
uv run python scripts/medagentbench/generate_harbor_tasks.py \
  --input-json data/medagentbench/test_data_v2.json \
  --output-root harbor_tasks/medagentbench

# 3) Export Codex auth for Harbor
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

# 4) Run the Harbor meta-task
uv run harbor run -c jobs/medagentbench_meta.yaml
```

## Harbor Debug Workflow

For step-by-step debugging of the generated Harbor task, use the helpers under `debug/`.

```bash
# Build and start the Harbor task environment
bash debug/harbor/build-task-env.sh
bash debug/harbor/up-task-env.sh

# Non-agent smoke path
bash debug/harbor/medagentbench/smoke-meta-task.sh

# Manual agent path
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
bash debug/harbor/medagentbench/run-manually.sh
```

See `debug/README.md` for the detailed breakdown.

## Transitional Legacy Path

The following commands still exist temporarily, but they are not the canonical MedAgentBench flow anymore:

```bash
uv run python scripts/medagentbench/import_tasks.py \
  --input data/medagentbench/test_data_v2.json \
  --funcs-json data/medagentbench/funcs_v1.json \
  --output-root tasks \
  --split std

uv run python run.py --task medagentbench --split std --max-tasks 3
uv run python scripts/medagentbench/evaluate.py --task medagentbench --results <results.jsonl>
```

Use those only when you need to compare against the old path during migration.
