# MedAgentBench Scripts

This directory contains MedAgentBench-specific operational scripts.

- `setup.sh`: idempotent asset bootstrap and schema validation for `benchmarks/medagentbench/assets/`
- `fhir_up.sh`: starts the Docker Compose FHIR runtime and waits for health on `http://localhost:8080/metadata`
- `fhir_down.sh`: stops Docker Compose FHIR runtime
- `import_tasks.py`: converts source task JSON into canonical YAML manifests
