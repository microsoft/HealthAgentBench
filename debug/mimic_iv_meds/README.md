# MIMIC-IV MEDS Debug

Use the generic Harbor debug workflow in `debug/README.md` with these benchmark-specific settings:

- `HB_TASK_DIR=tasks/mimic_iv_meds`
- `HB_PROJECT_NAME=mimic-iv-meds-debug`

The task expects the agent to work inside `/workspace/MIMIC_IV_MEDS`, set up the repo with `uv`, create a separate custom extraction config, run the pipeline on `/workspace/staged_demo/raw_input`, and write outputs under `/workspace/output/MEDS_cohort`.
