# MIMIC-IV MEDS Extraction ETL

Use the codebase at `/workspace/MIMIC_IV_MEDS` to run its ETL pipeline on the demo input at `/workspace/staged_demo/raw_input`.

Inspect the repository, use `uv` from the repo root to install and run the pipeline, and write the final MEDS cohort under `/workspace/output/MEDS_cohort`.

Create a new extraction config at `/workspace/MIMIC_IV_MEDS/src/MIMIC_IV_MEDS/configs/custom_event_configs.yaml` and use that new config for the ETL run.

Leave the default config at `/workspace/MIMIC_IV_MEDS/src/MIMIC_IV_MEDS/configs/event_configs.yaml` unchanged.

The new config must produce a customized extraction so that the final MEDS cohort:

- records admission-time `insurance`, `language`, `marital_status`, and `race` as separate events at the admission timestamp
- uses a dedicated `CHARTEVENT//...` code family for ICU chart events instead of folding them into the generic `LAB//...` namespace
- uses an `OMR//...` code family for OMR measurements

You may use `/workspace/output` for intermediate outputs.

Submission rules:

- Do not modify files under `/tests`.
- The task is complete only when the ETL run succeeds and the expected MEDS files are present.
