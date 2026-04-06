# MIMIC-IV MEDS Extraction ETL

You are working inside a task environment that contains:

- a pinned checkout of the upstream `MIMIC_IV_MEDS` repo at `/workspace/MIMIC_IV_MEDS`
- pre-staged open MIMIC-IV demo inputs at `/workspace/staged_demo/raw_input`
- a task-local helper script at `/workspace/scripts/patch_meds_transforms_lock.py`
- an output root at `/workspace/output`
- `uv` already installed in the container

Your goal is to inspect the upstream repo, set up its runtime environment using `uv`, and run the ETL pipeline successfully on the pre-staged MIMIC-IV demo data.

Expected workflow:

1. Read `/workspace/MIMIC_IV_MEDS/README.md` and inspect the repo structure.
2. From `/workspace/MIMIC_IV_MEDS`, create the runnable environment with `uv sync`.
3. Apply the task-local compatibility patch:
   - `python /workspace/scripts/patch_meds_transforms_lock.py /workspace/MIMIC_IV_MEDS/.venv`
4. Run the ETL pipeline against the staged demo input using `uv run` from the repo root.
5. Write the final MEDS output under `/workspace/output/MEDS_cohort`.

Use this command shape from the repo root once the environment is set up:

```bash
uv run MEDS_extract-MIMIC_IV
  root_output_dir=/workspace/output
  raw_input_dir=/workspace/staged_demo/raw_input
  pre_MEDS_dir=/workspace/output/pre_MEDS
  MEDS_cohort_dir=/workspace/output/MEDS_cohort
  do_download=False
  do_copy=True
  do_overwrite=True
```

Submission rules:

- Do not modify files under `/tests`.
- The verifier expects a repo-local `uv` environment at `/workspace/MIMIC_IV_MEDS/.venv`.
- The verifier expects the final MEDS cohort under `/workspace/output/MEDS_cohort`.
- The task is complete only when the ETL run succeeds and the expected MEDS files are present.
