# Chest CT Multi-Abnormality Classification

Patient-level chest-CT abnormality detection benchmark built on the CT-RATE
dataset (Hamamci et al., 2024). Ten Harbor subtasks, one per CT volume; the
agent reads `/workspace/data/scan.nii.gz` and a per-volume label list at
`/workspace/data/labels.txt`, decides yes/no for each requested label, and
writes predictions to `/workspace/submission/predictions.txt`.

## Canonical sources and runners

- Upstream dataset (gated): <https://huggingface.co/datasets/ibrahimhamamci/CT-RATE>
- License: OpenRAIL — host must accept the access agreement before downloads succeed.
- Canonical Harbor task generator: `scripts/ct_abnormality/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/ct_abnormality/`
- Per-benchmark assets: `scripts/ct_abnormality/assets/` (the `raw_cache/` subdirectory
  is gitignored — only `manifest.yaml` is committed).
- Harbor job: `jobs/ct_abnormality.yaml`
- Debug helpers: `debug/ct_abnormality/`
- Design notes: `design/related_work/ct_abnormality.md` and `.agent/plans/ct_abnormality.md`

## Hugging Face access (required)

CT-RATE is OpenRAIL-gated. **Without a valid Hugging Face token, every
download in this benchmark will fail with HTTP 403.**

Setup, once per host:

1. Visit <https://huggingface.co/datasets/ibrahimhamamci/CT-RATE> while signed
   in to your Hugging Face account and click *Agree and access repository*.
2. Provision a read token at <https://huggingface.co/settings/tokens>.
3. Add it to the repo-root `.env` file (gitignored):

       HF_TOKEN="hf_..."

The per-task `bootstrap` service reads `HF_TOKEN` from `.env` via
`env_file: ../../../../.env` in its `docker-compose.yaml`, so a one-click
`uv run harbor run -c jobs/ct_abnormality.yaml` needs no `export` and no
host-side `huggingface-cli login`. The credential is given to `bootstrap`
only — `main` (where the agent runs) never receives it, so the download
token cannot leak to the agent. If `HF_TOKEN` is empty the bootstrap exits
with a clear message naming the access URL.

The host-side asset downloader (`scripts/ct_abnormality/download_volumes.py`,
used for optional pre-staging) reads the token with the precedence `HF_TOKEN`
env var first, otherwise `~/.cache/huggingface/token`.

## How the benchmark works

- **Manifest** (`scripts/ct_abnormality/assets/manifest.yaml`) pins only the 10
  volume IDs (and a density `bucket`). It contains **no gold labels and no report
  text** — so the gated CT-RATE answer key / reports are never committed.
- **Runtime gold derivation.** Gold is reconstructed in-container at task
  bootstrap by `scripts/ct_abnormality/gold_derivation.py`, which downloads the
  volume's paired radiology report and applies a hardcoded set of **unambiguous
  report phrases** (`finding -> present/absent`). For each of the 17 evaluated
  findings:
  - a *present* phrase (and no *absent* phrase) → gold 1;
  - an *absent* phrase (and no *present* phrase) → gold 0;
  - both match (intra-report conflict, e.g. effusion present on one side, absent
    on the other) **or** neither matches → the finding is **dropped** (not
    scored). So only findings the report addresses unambiguously are retained
    (4–12 per volume).
  The derived polarity always agrees with CT-RATE's silver label for retained
  findings — the rules only *abstain* on ambiguous cases, never contradict
  silver. The verifier reads the runtime-written `tests/gold.json` (gitignored).
- **Silver-label filtering + manual review.** The phrase-identification rules
  act as a *filter* over CT-RATE's silver (model-predicted) labels: they keep
  only findings the paired report states unambiguously and abstain on the rest.
  On top of this automated filtering, the labels for **all 10 selected volumes
  were thoroughly reviewed by hand** against the reports to confirm correctness.
  So the gold for these cases is human-verified, not silver-trusted — the phrase
  rules make derivation reproducible, and the manual review guarantees the
  retained labels are right.
- **Per-volume reward.** Binary `1.0` iff every retained label matches gold;
  `0.0` otherwise. The agent is asked only about the retained labels for the
  volume, so the "perfect prediction" bar is well-defined.
- **Cross-volume aggregate.** Per-disease F1 is computed across the volumes
  that retained the disease (volumes that didn't mention a disease do not
  contribute to its TP/FP/FN). Macro-F1 averages across the 17 evaluated
  diseases; micro-F1 pools across all (volume, disease) pairs.
- **Categories scored.** 17 of CT-RATE's 18 abnormalities (`gold_derivation.FINDINGS`);
  Pulmonary fibrotic sequela is excluded. See `.agent/plans/ct_abnormality.md`
  decision log for details.

## Bootstrapping the cache

Stage all 10 volumes into the host cache once:

    uv run python scripts/ct_abnormality/download_volumes.py

That populates `scripts/ct_abnormality/assets/raw_cache/<volume_name>.nii.gz`
(~100–350 MB each, ~3.5 GB total). The cache is gitignored. Each per-task
`bootstrap` service falls back to downloading its own volume (using `HF_TOKEN`
from `.env`) if it finds the volume missing at run time, so a missing host
cache does not block a Harbor run — it only makes the first run slower.

## Generating Harbor tasks

    uv run python scripts/ct_abnormality/generate_harbor_tasks.py

Produces 10 task directories under `tasks/ct_abnormality/valid_<patient>_<scan>_<idx>/`
— named after the upstream CT-RATE volume stem so a human reader can trace
back to the original scan and report. Each task directory contains:

- `task.toml` — Harbor task config (`allow_internet=true` so the agent can
  install Python libraries; 8 GB storage to fit the volume).
- `instruction.md` — agent-facing prompt with input/output paths and rules.
- `environment/Dockerfile` — Python 3.12 base with `nibabel`, `pillow`,
  `huggingface_hub` pre-installed so the agent can read NIfTI files and
  render slices without `pip install` time. No `ENTRYPOINT` / `CMD` —
  Harbor's base compose layer overrides `main`'s command to
  `sleep infinity` to keep the container alive.
- `environment/bootstrap.sh` — runs in a separate compose service. Pulls
  the volume **and the validation reports CSV** from Hugging Face on cache miss
  (under a global host-side `flock` so concurrent task containers don't hammer
  the CDN), freezes cached files read-only, runs `gold_derivation.py` to derive
  this volume's gold from its report (writing `tests/gold.json` + the agent's
  `/workspace/data/labels.txt`), copies the volume to
  `/workspace/data/scan.nii.gz`, and exits 0.
- `environment/gold_derivation.py` — copy of the phrase-rule module, run by the
  bootstrap to derive gold at run time.
- `environment/docker-compose.yaml` — two services and a named volume. All
  host paths are **repo-relative** (`../../../../`), so the generated tasks
  carry no absolute host path and run unchanged on any machine:

      services:
        main:                   # the agent runs here
          build: ...            # only main builds; bootstrap reuses the image
          image: ${PROJECT}-img
          depends_on:
            bootstrap:
              condition: service_completed_successfully
        bootstrap:              # one-shot data staging + gold derivation
          image: ${PROJECT}-img
          env_file:
            - ../../../../.env  # HF_TOKEN; bootstrap-only, never reaches main
          volumes:
            - ../../../../scripts/ct_abnormality/assets/raw_cache:/data/_cache:rw
            - ../tests:/tests:rw   # bootstrap writes the runtime gold.json here
            - workspace-data:/workspace/data
          command: ["/bin/bash", "/bootstrap.sh"]
      volumes:
        workspace-data:

  Harbor invokes `docker compose up --detach --wait` which respects the
  `service_completed_successfully` condition, so by the time it execs the
  agent into `main` the data is already staged. Synchronization is entirely
  at the compose layer (mirrors `tasks/medagentbench/`); there are no
  per-`/workspace/` sentinel files and the installed-agent wrappers
  (`codex.py`, `claude_code.py`) are bit-identical to `origin/main`.
- `tests/gold.json` — **not committed**; written by the bootstrap at run time
  (gitignored) from the rule-derived gold.

## Running the benchmark

    export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"   # for codex agents
    uv run harbor run -c jobs/ct_abnormality.yaml

The Harbor job runs both Codex (`gpt-5.5`) and Claude Code (`claude-opus-4-7`)
agents with `n_concurrent_trials: 2` and `n_attempts: 1`.

## Tests

    uv run pytest tests/test_ct_abnormality_evaluator.py \
                  tests/test_ct_abnormality_aggregate.py \
                  tests/test_ct_abnormality_generator.py -v

## Debug

See `debug/ct_abnormality/README.md` for the manual-replay path and failure-class
triage.
