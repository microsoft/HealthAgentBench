# MIMIC-CXR Report Generation

This directory contains the Harbor-first integration for the MIMIC-CXR
radiology report generation benchmark task. Each task is one patient: the
agent sees the patient's prior chest-X-ray studies (JPGs + reports) and
must produce FINDINGS and IMPRESSION for a single target study given only
its images and the non-generated sections of its report.

## Canonical Source and Canonical Runner

- Canonical upstream source: PhysioNet `mimic-cxr` v2.1.0 (reports) +
  `mimic-cxr-jpg` v2.1.0 (images + split CSV) — credentialed access
- Canonical Harbor task generator: `scripts/xray_report_gen/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/xray_report_gen/`
- Per-benchmark asset cache: `scripts/xray_report_gen/assets/` (gitignored)
- Verifier-side metric aggregator: `scripts/xray_report_gen/aggregate_metric.py`

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

The benchmark ships **5 curated cases** (`case_01..case_05`); the
ground-truth reports were manually reviewed for clinical accuracy. Each
case has ≥1 prior study; every MIMIC prior for each patient is included
via metadata. Per-trial reward is binary: **1 iff CheXprompt** (Microsoft's
GPT-4 / gpt-5.x judge) **reports zero clinically-significant errors** in
the agent's FINDINGS vs. the gold, else 0. Aggregator emits mean reward
(= pass rate) + integer pass count via a `uv-script` metric hook.

## Canonical Workflow

> **Credentials required.** Two sets, both loaded from the repo-root
> `.env` automatically (the per-task `docker-compose.yaml` declares
> `env_file: ../../../../.env`, so no manual `export` is needed):
>
> * **PhysioNet** (`PN_USER` / `PN_PASS`) — credentialed access to MIMIC-CXR
>   reports and JPG images. Used by `setup.sh` and the bootstrap service.
> * **CheXprompt verifier model** — drives the verifier inside the trial
>   container. Supports both Azure OpenAI and vanilla OpenAI; whichever
>   set of vars is present in `.env` wins. The agent process never sees
>   these — they're forwarded to the verifier step only.
>
> **Default model: `gpt-5.4`.** If `CHEXPROMPT_DEPLOYMENT` (or its alias
> `AZURE_OPENAI_DEPLOYMENT`) is not set, the verifier hardcodes
> `gpt-5.4` as the deployment / model name. For Azure, your deployment
> alias must point at a gpt-5.4-capable resource.
>
> ### Azure OpenAI (recommended)
>
> Set in `.env`:
>
> ```
> AZURE_OPENAI_API_KEY=<your-azure-key>
> AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
> AZURE_OPENAI_API_VERSION=2024-02-15-preview
> AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>    # optional, defaults to "gpt-5.4"
> ```
>
> The verifier also accepts the legacy openai-SDK aliases
> (`OPENAI_API_BASE` for endpoint, `OPENAI_API_VERSION` for version,
> `OPENAI_API_KEY` for key, `CHEXPROMPT_DEPLOYMENT` for deployment) —
> Azure-canonical names take priority when both are set. Azure mode
> activates whenever endpoint + version + key are all present.
>
> ### Vanilla OpenAI (fallback)
>
> Set in `.env`:
>
> ```
> OPENAI_API_KEY=<your-key>
> OPENAI_BASE_URL=https://api.openai.com/v1   # optional; default if unset
> CHEXPROMPT_DEPLOYMENT=gpt-4o                # optional; default is gpt-5.4
> ```
>
> ### Model parameter handling
>
> `gpt-5.x` deployments (the default `gpt-5.4`) require
> `max_completion_tokens` instead of `max_tokens` and don't accept
> `temperature` / `top_p` / `frequency_penalty` / `presence_penalty`.
> The verifier auto-adapts when the deployment name starts with
> `gpt-5`. If your Azure deployment alias doesn't start with `gpt-5`
> but the underlying model is gpt-5.x, name the deployment with a
> `gpt-5*` prefix so the adaptation triggers.

```bash
# 0) Optional — Codex login (if running the agent under Harbor's Codex
#    adapter). Everything else is read from .env at run time.
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

# 1) Download dataset-wide PhysioNet assets (reports zip, metadata CSV,
#    split CSV, and CheXpert label CSV).
bash scripts/xray_report_gen/setup.sh

# 2) Generate the canonical Harbor task tree. ``--curated`` builds the
#    hardcoded 10-case set (``CURATED_CASES`` in
#    ``generate_harbor_tasks.py``) — patients whose target FINDINGS
#    were manually reviewed for clinical accuracy. Add ``--purge`` to
#    wipe any stale ``case_NN`` dirs at --output-root first.
#
#    Alternative modes (not used for the shipped 10-case suite):
#      --sample-size N           random sample of N eligible patients
#      --selected-subject-ids …  comma-separated patient IDs
#      --disease-stratified      14 patients, 1 per CheXpert category
#      --tiered-stratified       10-patient severity-tiered sample
uv run python scripts/xray_report_gen/generate_harbor_tasks.py \
  --output-root tasks/xray_report_gen --curated --purge

# 3) Run the Harbor task. The two-service docker-compose pattern's
#    `bootstrap` container downloads missing assets (per-patient JPGs
#    and the target report used by the verifier) from PhysioNet on
#    first use, so steps 1+2 are optional after credentials are set.
uv run harbor run -c jobs/xray_report_gen.yaml
```

## Evaluation

Reward signal: **CheXprompt** (https://github.com/microsoft/chexprompt)
prompts an Azure OpenAI GPT-4 deployment to count clinical errors in 6
categories × 2 severity tiers for each generated FINDINGS section vs.
the gold FINDINGS. A trial **passes** (reward 1.0) iff a majority of
5 CheXprompt votes report zero *clinically-significant* errors;
otherwise the trial fails (reward 0.0). The gold FINDINGS is parsed
at verifier time from the target study's full report (staged at
`/tests/target_report.txt` by the `bootstrap` compose service via
the credentialed PhysioNet download of `mimic-cxr-reports.zip`).
The curated 10 cases have been manually reviewed for clinical
accuracy of the gold. The gold text is never checked into this repo
and never exposed to the agent.

## Concurrency

Docker's default network-address pool caps at ~31 simultaneous bridge
networks, and each Harbor trial creates one. The job config pins
`n_concurrent_trials: 10` (= the curated case count, so a single-attempt
sweep can fan out fully) with headroom for parallel sweeps via
`scripts/run_harbor_baselines_multitask.py`. See inline comments in
`jobs/xray_report_gen.yaml` for details.

Setup/generator/entrypoint all flock on the same lock
(`assets/.locks/mimic-cxr-setup.lock` host-side, visible inside the
container as `/data/_src/jpg_root/.bootstrap.lock`) so concurrent trials
safely share the partial download. Downloads are idempotent (`wget -c -N`).

## Harbor Artifacts

The Harbor job at `jobs/xray_report_gen.yaml` retains this artifact after
each run for error analysis:

- `/workspace/submission.json` — the agent's authored FINDINGS + IMPRESSION

## Manual Replay

For the human replay path used to distinguish agent failures from
task / environment / verifier failures, see
`debug/xray_report_gen/README.md`.

## References

- **MIMIC-CXR paper**: https://doi.org/10.1038/s41597-019-0322-0
- **MIMIC-CXR v2.1.0**: https://physionet.org/content/mimic-cxr/2.1.0/
- **MIMIC-CXR-JPG v2.1.0**: https://physionet.org/content/mimic-cxr-jpg/2.1.0/
- **CheXprompt** (verifier model): https://github.com/microsoft/chexprompt
- **Related-work note**: `design/related_work/mimic_cxr_report_generation.md`
