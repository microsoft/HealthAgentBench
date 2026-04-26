# MIMIC-CXR Report Generation

This directory contains the Harbor-first integration for the MIMIC-CXR
radiology report generation benchmark task. Each task is one patient: the
agent sees the patient's prior chest-X-ray studies (JPGs + reports) and
must produce FINDINGS and IMPRESSION for a single target study given only
its images and the non-generated sections of its report.

## Canonical Source and Canonical Runner

- Canonical upstream source: PhysioNet `mimic-cxr` v2.1.0 (reports) +
  `mimic-cxr-jpg` v2.1.0 (images + split CSV) — credentialed access
- Canonical Harbor task generator: `scripts/mimic_report_gen/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/mimic_report_gen/`
- Per-benchmark asset cache: `scripts/mimic_report_gen/assets/` (gitignored)
- Verifier-side metric aggregator: `scripts/mimic_report_gen/aggregate_metric.py`

## Benchmark Shape

This benchmark evaluates whether an agent can:

1. inspect a longitudinal patient directory at `/data/patient/` containing
   timestamped folders of prior studies (JPG images + `report.txt`) plus
   one target-study folder (images only, no report)
2. view images via repeated tool calls and integrate visual observation
   with the textual history from prior reports
3. produce FINDINGS and IMPRESSION for the target study, consistent with
   documented chronic findings and the agent-visible non-generated
   sections (EXAMINATION, INDICATION, HISTORY, TECHNIQUE, COMPARISON)
4. emit a valid `/workspace/submission.json` the verifier can score

A patient is eligible if they have 2+ studies with images + reports on
disk, their target (latest) study is in the MIMIC-CXR-JPG `test` split,
and the target report has non-empty FINDINGS + IMPRESSION with clear
section headers. Evaluation reports per-trial BLEU-4 and ROUGE-L plus
pooled CheXbert F1-14 via a `uv-script` aggregator.

## Canonical Workflow

> **Credentials required.** PhysioNet downloads need your credentialed-access
> account. Export `PN_USER` / `PN_PASS` once in your shell — the same
> variables are reused by `setup.sh`, the generator, and the container
> entrypoint.

```bash
# 0) Credentials + Codex login (same vars reused by all three steps below)
export PN_USER=<physionet_username>
export PN_PASS=<physionet_password>
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

# 1) Download the two dataset-wide PhysioNet assets (idempotent, flock-guarded).
bash scripts/mimic_report_gen/setup.sh

# 2) Generate the Harbor task tree + download the per-task JPG subset.
#    Default: every eligible patient. Use --sample-size N to cap; use
#    --selected-subject-ids a,b,c to target specific patients.
uv run python scripts/mimic_report_gen/generate_harbor_tasks.py \
  --output-root tasks/mimic_report_gen

# 3) Run the Harbor task. You can skip step 1 and step 2 and directly run this step. If we did not download the assets from step 1 and 2. This step will automatically download all necessary assets on the fly. 
uv run harbor run -c jobs/mimic_report_gen.yaml
```

## Concurrency

Docker's default network-address pool caps at ~31 simultaneous bridge
networks, and each Harbor trial creates one. The job config pins
`n_concurrent_trials: 15` to leave headroom when running two models in
parallel via `scripts/run_harbor_baselines_multitask.py`. See inline
comments in `jobs/mimic_report_gen.yaml` for details.

Setup/generator/entrypoint all flock on the same lock
(`assets/.locks/mimic-cxr-setup.lock` host-side, visible inside the
container as `/data/_src/jpg_root/.bootstrap.lock`) so concurrent trials
safely share the partial download. Downloads are idempotent (`wget -c -N`).

## Harbor Artifacts

The Harbor job at `jobs/mimic_report_gen.yaml` retains this artifact after
each run for error analysis:

- `/workspace/submission.json` — the agent's authored FINDINGS + IMPRESSION

## Manual Replay

For the human replay path used to distinguish agent failures from
task / environment / verifier failures, see
`debug/mimic_report_gen/README.md`.

## References

- **MIMIC-CXR paper**: https://doi.org/10.1038/s41597-019-0322-0
- **MIMIC-CXR v2.1.0**: https://physionet.org/content/mimic-cxr/2.1.0/
- **MIMIC-CXR-JPG v2.1.0**: https://physionet.org/content/mimic-cxr-jpg/2.1.0/
- **CheXbert labeler**: https://arxiv.org/abs/2004.09167
- **Related-work note**: `design/related_work/mimic_cxr_report_generation.md`
