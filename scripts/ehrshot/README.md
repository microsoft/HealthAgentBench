# EHRSHOT — Few-Shot Clinical Prediction on Longitudinal EHR

Stanford SHAH lab's few-shot benchmark over 6,739 longitudinal EHR patient
timelines from a STARR-OMOP extract (Wornow et al., 2023, NeurIPS Datasets &
Benchmarks). Fifteen Harbor subtasks, one per EHRSHOT prediction task. The
agent reads `/workspace/data/train_labels.csv`, `/workspace/data/val_labels.csv`,
`/workspace/data/test_examples.csv`, and a leak-proof per-task slice of the
longitudinal event log at `/workspace/data/events.csv`; submits a probability
per test row to `/workspace/submission/predictions.csv`; the verifier scores
AUROC against the held-out test labels and reports pass/fail against the
published `count + LightGBM` baseline.

## Canonical sources and runners

- Upstream dataset (gated): <https://redivis.com/datasets/53gc-8rhx41kgt>
- Upstream pipeline + paper: <https://github.com/som-shahlab/ehrshot-benchmark>
  (Wornow et al., 2023, [`arXiv:2307.02028`](https://arxiv.org/abs/2307.02028))
- License: Redivis-gated DUA — host must accept the access agreement before
  downloads succeed.
- Canonical Harbor task generator: `scripts/ehrshot/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/ehrshot/`
- Per-benchmark assets: `scripts/ehrshot/assets/` (the `EHRSHOT_ASSETS/`
  bundle is gitignored — only `task_configs.yaml` is committed).
- Host-side bundle downloader: `scripts/ehrshot/download.py`
- Host-side baseline reproducers (mirror EHRSHOT's `7_eval_finetune.py`):
  `scripts/ehrshot/reproduce_all_tasks.py` (count + LightGBM) and
  `scripts/ehrshot/reproduce_clmbr.py` (CLMBR + lr_lbfgs)
- Harbor job: `jobs/ehrshot_smoke.yaml` (single-task smoke run); use
  `scripts/run_harbor_baselines_multitask.py` for the full 15-task sweep.

## Redivis access (required)

EHRSHOT is Redivis-gated. **Without a valid Redivis API token, the bundle
download in this benchmark will fail with HTTP 401.**

Setup, once per host:

1. Visit <https://redivis.com/datasets/53gc-8rhx41kgt> while signed in to
   your Redivis account and accept the data-use agreement.
2. Provision a read token at *Settings → API tokens* in the Redivis web UI.
3. Cache the token at `~/.redivis/api_token`:

```bash
mkdir -p ~/.redivis
echo 'rdv_xxxxxxxxxxxxxxxxxxxxxxxx' > ~/.redivis/api_token
chmod 600 ~/.redivis/api_token
```

The host-side downloader (`scripts/ehrshot/download.py`) and the per-task
container `bootstrap.sh` both read the token via the same precedence:
`REDIVIS_API_TOKEN` env var first, otherwise `~/.redivis/api_token`. If
neither is found, the downloader exits with a clear message naming the
access URL, and the bootstrap prints the same message before main boots.

**The file must exist on host even when the cache is warm** — Docker resolves
the bind-mount source at container creation time and errors out if the path
doesn't exist.

## How the benchmark works

- **Fifteen prediction tasks**, all binary AUROC except chexpert (mean AUROC
  across 14 binary subtasks):
  - **Operational** (predicted at admission/discharge): `guo_icu` (ICU
    transfer), `guo_los` (LOS ≥ 7 days), `guo_readmission` (30-day readmit)
  - **Lab abnormality** (predicted at lab order time): `lab_anemia`,
    `lab_hyperkalemia`, `lab_hypoglycemia`, `lab_hyponatremia`,
    `lab_thrombocytopenia`. EHRSHOT's raw 4-class severity labels are
    binarized at `value >= 1` to match the published baseline.
  - **New diagnosis** within 365 days (predicted at last inpatient discharge
    before first qualifying ICD): `new_acutemi`, `new_celiac`,
    `new_hyperlipidemia`, `new_hypertension`, `new_lupus`, `new_pancan`.
  - **Multilabel radiology** (predicted at chest-X-ray order time):
    `chexpert` — 14 independent findings.
- **Patient-level splits**, identical across all 15 tasks: 2,295 train /
  2,232 val / 2,212 test. Sourced from
  `EHRSHOT_ASSETS/splits/person_id_map.csv`.
- **Last-per-patient test subset.** Most tasks have multiple labeled rows
  per patient (e.g., a patient can have many admissions in `guo_icu`).
  Per-row evaluation is sound but lets the same patient's later events
  legitimately inform earlier rows. To keep the leak-proof contract
  unambiguous, we subset the test split to **one row per patient — the
  latest `prediction_time`**. The benchmark gate is computed on that
  subset. See `auroc_last` columns in `baselines.csv`.
- **Leak-proof events.csv.** For each test patient `P` in the subset, only
  events with `start < T_last(P)` are visible in `/workspace/data/events.csv`.
  Train + val patients get full timelines (their labels are visible
  anyway). Multi-row test patients excluded from the subset are dropped
  entirely. Slicing happens at run time inside the bootstrap container.
- **Pass gate**: `count + LightGBM` AUROC on the last-per-patient subset,
  reproduced bit-for-bit from EHRSHOT's `7_eval_finetune.py` and stored at
  `tasks/ehrshot/<task>/tests/baseline.json`. The `clmbr + lr_lbfgs`
  AUROC is also recorded under `clmbr_baseline_auroc` for reference (not
  the active gate).
- **Per-trial reward**: `reward.json` contains `reward` (binary 1.0 if the
  agent's AUROC exceeds the baseline, else 0.0), `success` (same as int),
  `auroc`, `auprc`, `brier`, and `baseline_auroc`. The launcher's
  `Successes` column counts pass trials; `auroc` is the agent's actual
  score.

## Bootstrapping the cache

Stage the full EHRSHOT bundle into the host cache once:

```bash
uv run python scripts/ehrshot/download.py
```

That populates `scripts/ehrshot/assets/EHRSHOT_ASSETS/` (~4 GB compressed
download → ~17 GB extracted). The cache is gitignored. Per-task container
bootstraps fall back to the same Redivis download when they find a missing
bundle at run time, so a missing host cache does not block a Harbor run —
it only makes the first task on that host slower (~5 min extra).

Layout:

```text
scripts/ehrshot/assets/EHRSHOT_ASSETS/
    data/ehrshot.csv               # 3.2 GB OMOP-derived event log, 41M rows
    splits/person_id_map.csv       # canonical patient → train/val/test
    benchmark/<task>/...           # per-task labels + few-shot configs
    features/count_features.pkl    # pre-computed sparse count features (4 GB)
    features/clmbr_features.pkl    # CLMBR foundation-model embeddings
    results/<task>/all_results.csv # published baseline AUROCs
    models/clmbr/                  # CLMBR model weights (~1 GB; unused unless fine-tuning)
```

## Generating Harbor tasks

```bash
uv run python scripts/ehrshot/generate_harbor_tasks.py
```

Reads `scripts/ehrshot/assets/task_configs.yaml` (committed) and produces
15 task directories under `tasks/ehrshot/<task_id>/` named after the
EHRSHOT task id (e.g. `guo_icu`, `lab_anemia`, `chexpert`). Each task
directory contains:

- `task.toml` — Harbor task config (16 CPU, 64 GB RAM, internet enabled,
  1-hour agent budget; `gpus = 0` by default — bump to `1` on GPU hosts).
- `instruction.md` — agent-facing prompt with input/output paths, label
  semantics, leakage rule, and scoring contract.
- `environment/Dockerfile` — Python 3.12 base with `numpy`, `pandas`,
  `scipy`, `scikit-learn`, `lightgbm`, `xgboost`, `pyarrow`, and `redivis`
  pre-installed. Bakes `stage_data.py` + `evaluate.py` into the image.
- `environment/bootstrap.sh` — runs in a separate compose service.
  Downloads the bundle from Redivis on cache miss (under a global host-side
  `flock` so concurrent task containers serialize the download), then
  invokes `stage_data.py` to slice per-task labels and the leak-proof
  events.csv into the shared workspace volume.
- `environment/docker-compose.yaml` — two services and a named volume.
  All host paths are repo-relative or `${HOME}`-templated so the repo is
  portable across users / machines:

      services:
        main:                   # the agent runs here
          build: ...
          image: ${PROJECT}-img
          depends_on:
            bootstrap:
              condition: service_completed_successfully
        bootstrap:              # one-shot data staging
          image: ${PROJECT}-img
          volumes:
            - ../../../../scripts/ehrshot/assets:/data/_cache:rw
            - ${HOME}/.redivis/api_token:/root/.redivis/api_token:ro
            - workspace-data:/workspace/data:rw
            - ../tests:/tests:rw
          command: ["/bin/bash", "/bootstrap.sh"]
      volumes:
        workspace-data:

  Harbor invokes `docker compose up --wait` which respects the
  `service_completed_successfully` condition, so by the time it execs the
  agent into `main` the data is already staged.
- `tests/baseline.json` — count+gbm pass gate + clmbr reference, baked in
  at generation time (read from `scripts/ehrshot/assets/baselines.csv`).
- `tests/test_labels.csv` — **not committed**, written at run time by the
  bootstrap (gitignored via `tasks/ehrshot/*/tests/test_labels.csv`).

## Running the benchmark

Single-task smoke run:

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"   # for codex agents
uv run harbor run -c jobs/ehrshot_smoke.yaml
```

Full 15-task sweep:

```bash
uv run python scripts/run_harbor_baselines_multitask.py \
    --task-name ehrshot --task-path tasks \
    --harness codex --model gpt-5.4 \
    --reasoning-effort medium \
    --attempts 1 --concurrency 2 \
    --output-root /path/to/results/ehrshot \
    --artifact /workspace/submission/predictions.csv \
    --metric-to-report success \
    --metric-to-report reward \
    --metric-to-report auroc
```

The launcher writes per-task results to `/path/to/results/ehrshot/<run>/`
and renders a `## ehrshot` section into `paper/baselines.md`.

## Reproducing the published baselines

Two host-side scripts mirror EHRSHOT's `7_eval_finetune.py` exactly and
produce the per-task AUROC numbers used by the verifier gate:

```bash
uv run python scripts/ehrshot/reproduce_all_tasks.py   # count + LightGBM (~30 min)
uv run python scripts/ehrshot/reproduce_clmbr.py       # clmbr + lr_lbfgs (~1 min)
```

Outputs: `scripts/ehrshot/assets/baselines.csv` and `baselines_clmbr.csv`
with `auroc_full`, `auroc_last`, `auroc_first`, `auroc_single` per task,
plus per-row predictions under `scripts/ehrshot/assets/predictions{,_clmbr}/`.
Both scripts reproduce the published `EHRSHOT_ASSETS/results/<task>/all_results.csv`
numbers to 3–4 decimal places.

## Debug

See `debug/ehrshot/README.md` (TBD) for the manual-replay path and
failure-class triage.

## References

```bibtex
@inproceedings{wornow2023ehrshot,
  title     = {{EHRSHOT}: An {EHR} Benchmark for Few-Shot Evaluation of Foundation Models},
  author    = {Wornow, Michael and Thapa, Rahul and Steinberg, Ethan and Fries, Jason and Shah, Nigam},
  booktitle = {Advances in Neural Information Processing Systems},
  year      = {2023}
}
```
