# MIMIC-IV MEDS Extraction ETL

Use the codebase at `/workspace/MIMIC_IV_MEDS` to run its ETL pipeline on the demo input at `/workspace/staged_demo/raw_input`.

Inspect the repository, use `uv` from the repo root to install and run the pipeline, and write the final MEDS cohort under `/workspace/output/MEDS_cohort`.

Inspect the default extraction config at `/workspace/MIMIC_IV_MEDS/src/MIMIC_IV_MEDS/configs/event_configs.yaml`. Create a new config at `/workspace/MIMIC_IV_MEDS/src/MIMIC_IV_MEDS/configs/custom_event_configs.yaml` by copying that default config and editing the copy.

Leave the default config unchanged, and run the ETL with the new config instead of the default one.

The new config must produce a customized extraction so that the final MEDS cohort:

- no longer stores `insurance`, `language`, `marital_status`, or `race` as fields on the hospital admission event
- records each of those four admission-time demographics as its own event at the admission timestamp using the prefixes `INSURANCE//...`, `LANGUAGE//...`, `MARITAL_STATUS//...`, and `RACE//...`
- uses `OMR//...` for outpatient OMR measurements
- uses `HOSP_LAB//...` for hospital lab events from `hosp/labevents`
- uses `ICU_CHARTEVENT//...` for ICU chart events from `icu/chartevents`

You may use `/workspace/output` for intermediate outputs.

Submission rules:

- Do not modify files under `/tests`.
- The task is complete only when the ETL run succeeds and the expected MEDS files are present.
