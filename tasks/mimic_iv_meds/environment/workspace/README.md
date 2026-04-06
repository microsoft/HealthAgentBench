# MIMIC-IV MEDS Task Workspace

This workspace contains the pinned upstream repo checkout at `MIMIC_IV_MEDS/`.

Pinned upstream version:
- tag: `0.0.7`
- commit: `9699e0865b050325459b11f3c4e226a9dbe5b496`

Staged demo input lives under `staged_demo/raw_input/`.

Expected agent workflow:
1. `cd /workspace/MIMIC_IV_MEDS`
2. `uv sync`
3. `python /workspace/scripts/patch_meds_transforms_lock.py /workspace/MIMIC_IV_MEDS/.venv`
4. `uv run MEDS_extract-MIMIC_IV root_output_dir=/workspace/output raw_input_dir=/workspace/staged_demo/raw_input pre_MEDS_dir=/workspace/output/pre_MEDS MEDS_cohort_dir=/workspace/output/MEDS_cohort do_download=False do_copy=True do_overwrite=True`
