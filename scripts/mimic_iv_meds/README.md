# MIMIC-IV MEDS Extraction ETL

This directory contains the Harbor-first integration for the `MIMIC_IV_MEDS` benchmark task.

## Canonical Source and Canonical Runner

- Canonical upstream source: `MIMIC_IV_MEDS` tag `0.0.7`
- Canonical Harbor task generator: `scripts/mimic_iv_meds/generate_harbor_task.py`
- Canonical runnable task artifact: `tasks/mimic_iv_meds/`
- Verifier-side gold summary: `scripts/mimic_iv_meds/assets/gold_demo_summary.json`

## Benchmark Shape

This benchmark evaluates whether an agent can:

1. inspect the pinned upstream repo checkout
2. use `uv` inside the container to create the runnable environment
3. apply the task-local compatibility patch required for this benchmark environment
4. run the MEDS extraction pipeline on the pre-staged open MIMIC-IV demo input, including `root_output_dir=/workspace/output`
5. produce a valid MEDS cohort directory

## Canonical Workflow

```bash
# 1) Generate the Harbor task
uv run python scripts/mimic_iv_meds/generate_harbor_task.py \
  --output-root tasks/mimic_iv_meds

# 2) Run the Harbor task
uv run harbor run -c jobs/mimic_iv_meds.yaml
```

## Reference Summary Maintenance

The verifier uses a compact gold summary rather than full file hashing.

If the pinned upstream repo or the staged demo-input strategy changes, regenerate the summary from a known-good reference run:

```bash
uv run python scripts/mimic_iv_meds/build_reference_summary.py \
  --output-root /path/to/reference-run-root \
  --summary-out scripts/mimic_iv_meds/assets/gold_demo_summary.json
```
