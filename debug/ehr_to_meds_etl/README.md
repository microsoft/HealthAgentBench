# MIMIC-IV MEDS Debug

Use the generic Harbor debug workflow in `debug/README.md` with these benchmark-specific settings:

- `HB_TASK_DIR=tasks/ehr_to_meds_etl`
- `HB_PROJECT_NAME=mimic-iv-meds-debug`

The task expects the agent to work inside `/workspace/MIMIC_IV_MEDS`, set up the repo with `uv`, create a separate custom extraction config by copying and editing the default config, keep the packaged default config wiring pointed at `event_configs.yaml`, run the pipeline on `/workspace/staged_demo/raw_input`, and write outputs under `/workspace/output/MEDS_cohort`.

The verifier checks the final MEDS output against the gold summary, checks that the default config file and its packaged default wiring remain unchanged, and checks that the custom YAML satisfies the required admission-demographic split plus the exact prefixes `INSURANCE//...`, `LANGUAGE//...`, `MARITAL_STATUS//...`, `RACE//...`, `OMR//...`, `HOSP_LAB//...`, and `ICU_CHARTEVENT//...`.
