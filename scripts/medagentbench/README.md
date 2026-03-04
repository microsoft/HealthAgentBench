# MedAgentBench Scripts

This directory contains MedAgentBench-specific operational scripts.

- `setup.sh`: idempotent asset bootstrap for `benchmarks/medagentbench/assets/`
- `fhir_up.sh`: starts a local FHIR-compatible mock endpoint at `http://localhost:8080/metadata`
- `fhir_down.sh`: stops the local FHIR mock endpoint
- `import_tasks.py`: converts source task JSON into canonical YAML manifests
