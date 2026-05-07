# CT-RATE — Chest CT Multi-Abnormality Classification

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
3. Cache the token. Either approach works:
   - `huggingface-cli login` (writes `~/.cache/huggingface/token`).
   - `export HF_TOKEN="hf_..."` (the downloader checks the env var first).

The asset downloader (`scripts/ct_abnormality/download_volumes.py`) and the per-task
container `entrypoint.sh` both read the token via the same precedence:
`HF_TOKEN` env var first, otherwise `~/.cache/huggingface/token`. If neither
is found, the downloader exits with a clear message naming the access URL,
and the entrypoint prints the same message before the agent boots.

## How the benchmark works

- **Manifest** (`scripts/ct_abnormality/assets/manifest.yaml`) pins the 10 volumes,
  their density bucket, and the labels we evaluate. Each evaluated label has a
  `gold` value (0 or 1) and an `evidence` string — the verbatim quote from the
  paired physician report that justifies the value.
- **Strict report-derived gold.** CT-RATE ships predicted (silver) labels that
  disagree with the report text in places. The MedCLI integration ignores
  those and re-derives gold from the report under a strict exact-wording rule.
  Per volume, only labels whose value is unambiguously grounded in the report
  are retained (4–12 labels). Labels not retained are dropped from the
  verifier's view of that volume.
- **Per-volume reward.** Binary `1.0` iff every retained label matches gold;
  `0.0` otherwise. The agent is asked only about the retained labels for the
  volume, so the "perfect prediction" bar is well-defined.
- **Cross-volume aggregate.** Per-disease F1 is computed across the volumes
  that retained the disease (volumes that didn't mention a disease do not
  contribute to its TP/FP/FN). Macro-F1 averages across the 17 evaluated
  diseases; micro-F1 pools across all (volume, disease) pairs.
- **Categories scored.** 17 of CT-RATE's 18 abnormalities — Pulmonary fibrotic
  sequela was dropped because no volume retained it under the strict-wording
  rule. See `.agent/plans/ct_abnormality.md` decision log for details.

## Bootstrapping the cache

Stage all 10 volumes into the host cache once:

    uv run python scripts/ct_abnormality/download_volumes.py

That populates `scripts/ct_abnormality/assets/raw_cache/<volume_name>.nii.gz` (~1 GB
total). The cache is gitignored. Per-task container entrypoints fall back to
the same downloader if they find a missing volume at run time, so a missing
host cache does not block a Harbor run — it only makes the first run slower.

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
  the volume from Hugging Face on cache miss (under a global host-side
  `flock` so concurrent task containers don't hammer the CDN), freezes
  the cached file read-only, copies it to `/workspace/data/scan.nii.gz`
  via the shared workspace volume, writes `labels.txt`, and exits 0.
- `environment/docker-compose.yaml` — two services and a named volume:

      services:
        main:                   # the agent runs here
          build: ...            # only main builds; bootstrap reuses the image
          image: ${PROJECT}-img
          depends_on:
            bootstrap:
              condition: service_completed_successfully
        bootstrap:              # one-shot data staging
          image: ${PROJECT}-img
          volumes:
            - <host raw_cache>:/data/_cache:rw
            - ${HOME}/.cache/huggingface/token:/root/.cache/huggingface/token:ro
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
- `tests/gold.json` — verifier-only gold derived from the manifest.

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
