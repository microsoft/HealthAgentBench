# MIMIC-IV MEDS Extraction ETL

Use the codebase at `/workspace/MIMIC_IV_MEDS` to run its ETL pipeline on the demo input at `/workspace/staged_demo/raw_input`.

Inspect the repository, use `uv` from the repo root to install and run the pipeline, and write the final MEDS cohort under `/workspace/output/MEDS_cohort`.

You may use `/workspace/output` for intermediate outputs.

Submission rules:

- Do not modify files under `/tests`.
- The task is complete only when the ETL run succeeds and the expected MEDS files are present.
