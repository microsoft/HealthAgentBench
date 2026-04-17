# MIMIC-CXR Report Generation Harbor Task Scripts

This directory contains scripts for integrating the **MIMIC-CXR radiology
report generation** benchmark into the Harbor framework. Each task is one
patient: the agent sees the patient's prior chest-X-ray studies (JPGs +
reports) and must produce FINDINGS and IMPRESSION for a single target study
given only its images and the non-generated sections of its report.

## Overview

Source data is hosted on [PhysioNet](https://physionet.org/) and requires
credentialed access:

- `mimic-cxr` v2.1.0 — radiology report archive (`mimic-cxr-reports.zip`)
- `mimic-cxr-jpg` v2.1.0 — 512-px JPG images + train/val/test split CSV

Default task dataset: **every eligible patient** — a patient is eligible
if they have 2+ studies with images + reports present, their target
(latest) study falls in the MIMIC-CXR-JPG `test` split, and the target
report has non-empty FINDINGS + IMPRESSION. Use `--sample-size N` to cap.

## Canonical Files

| File | Purpose |
|---|---|
| `normalization.py` | Metadata loading, patient-study indexing, eligibility filters, sampling |
| `generate_harbor_tasks.py` | Harbor task artifact generator (one task dir per patient) |
| `harbor_evaluator.py` | Report-generation evaluation (text-based metrics) |
| `aggregate_metric.py` | Aggregate per-task evaluation results across the benchmark |
| `verify_meta_task.py` | Harbor verifier script (called after agent completion) |
| `setup.sh` | Download the two dataset-wide PhysioNet assets (reports zip + split CSV) |

## Data Layout

All source data lives under `scripts/mimic_report_gen/assets/`
(gitignored). Each task's docker-compose bind-mounts this folder into the
container so the entrypoint has direct access to images and reports.

```
scripts/mimic_report_gen/assets/
├── .locks/                                       # flock coordination
├── mimic-cxr/2.1.0/
│   └── mimic-cxr-reports.zip                     # all radiology reports
└── mimic-cxr-jpg/2.1.0/
    ├── mimic-cxr-2.0.0-split.csv.gz              # train/val/test split
    └── files/
        └── p<XX>/p<subject_id>/s<study_id>/<dicom_id>.jpg
```

Only the JPGs for patients referenced by generated tasks are downloaded —
the full dataset is ~4.7 TB, the per-task subset is orders of magnitude
smaller.

## Workflow (Manual Steps)

### 1. Setup: Download Dataset-Wide Assets

> **Credentials required.** PhysioNet downloads need your credentialed-access
> account. Export `PN_USER` and `PN_PASS` in your shell **before** running
> setup, task generation, or `harbor run` — the same variables are reused by
> all three steps:
>
> ```bash
> export PN_USER=<physionet_username>
> export PN_PASS=<physionet_password>
> ```

```bash
bash scripts/mimic_report_gen/setup.sh
```

This downloads the two files that every task needs regardless of which
patients are selected:

- `mimic-cxr-reports.zip`
- `mimic-cxr-2.0.0-split.csv.gz`

It is idempotent (`wget -c`) and flock-guarded at
`assets/.locks/mimic-cxr-setup.lock`. Per-patient JPGs are **not** fetched
here — they are fetched during task generation.

Environment variables:

| Var | Default | Purpose |
|---|---|---|
| `PN_USER` | *(required)* | PhysioNet username |
| `PN_PASS` | *(required)* | PhysioNet password |
| `MIMIC_CXR_DATA_ROOT` | `scripts/mimic_report_gen/assets` | Override data root |

### 2. Generate Harbor Task Artifacts (and Download Per-Task JPGs)

Task generation writes one Harbor task directory per patient under
`tasks/mimic_report_gen/`. Immediately after writing all task manifests,
the generator computes the per-patient JPG subset those tasks need,
diff-checks against `assets/mimic-cxr-jpg/2.1.0/files/`, and downloads any
missing JPGs from PhysioNet under the same flock.

> **Reminder:** `PN_USER` / `PN_PASS` must still be exported from step 1 so
> the generator can fetch the per-task JPG subset. If they are unset, task
> files are written but JPG download is skipped (with a warning), and task
> containers will attempt the download on first run.

Default run (every eligible patient, latest study as target):

```bash
uv run python scripts/mimic_report_gen/generate_harbor_tasks.py \
  --output-root tasks/mimic_report_gen
```

Capped sample size (deterministic with `--seed`, default 42):

```bash
uv run python scripts/mimic_report_gen/generate_harbor_tasks.py \
  --output-root tasks/mimic_report_gen \
  --sample-size 100
```

Specific patients (skips sampling):

```bash
uv run python scripts/mimic_report_gen/generate_harbor_tasks.py \
  --output-root tasks/mimic_report_gen \
  --selected-subject-ids 11022245,12595991
```

Each generated task dir contains the standard Harbor layout
(`task.toml`, `instruction.md`, `environment/`, `tests/`). The
`environment/docker-compose.yaml` mounts the assets folder into the
container at `/data/_src/jpg_root` and `/data/_src/reports_root`.

### 3. Run with Harbor

Each task container's `entrypoint.sh` re-runs the same flock-guarded
download logic for its own manifest. This means tasks can still bootstrap
themselves even if `setup.sh` or the generator's download step was
skipped.

> **Reminder:** `PN_USER` / `PN_PASS` must be exported in the shell that
> starts Harbor. `docker-compose.yaml` forwards them into the container
> (`PN_USER=${PN_USER:-}`, `PN_PASS=${PN_PASS:-}`); if they are unset at
> `harbor run` time and any required file is missing, the container will
> skip the download and fail loudly when it can't find the asset.

```bash
source .venv/bin/activate
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
export PN_USER=<physionet_username>      # same credentials as step 1
export PN_PASS=<physionet_password>
uv run harbor run -c jobs/mimic_report_gen.yaml
```

After bootstrap, the entrypoint materializes `/data/patient/` as
timestamped folders:

```
/data/patient/
├── manifest.json
├── 2171-10-14_23-34-21_s50078440/      # prior study
│   ├── <dicom_id>.jpg
│   └── report.txt
├── ...
└── 2176-06-07_19-52-05_s52391187/      # target study (no report.txt)
    └── <dicom_id>.jpg
```

## Task Format

### Input: benchmark_tasks.json (agent-visible)

```json
[
  {
    "task_id": "mimic_cxr_report_11022245_52391187",
    "subject_id": "11022245",
    "target_study": {
      "study_id": "52391187",
      "study_datetime": "2176-06-07 19:52:05",
      "procedure": "CHEST (PORTABLE AP)",
      "views": [{"dicom_id": "...", "view_position": "AP", "path": "..."}],
      "given_sections": {
        "EXAMINATION": "...",
        "INDICATION": "...",
        "HISTORY": "...",
        "TECHNIQUE": "...",
        "COMPARISON": "..."
      }
    },
    "history": [ /* prior studies with reports + images */ ],
    "instruction": "..."
  }
]
```

### Output: Harbor Submission Format

```json
[
  {
    "task_id": "mimic_cxr_report_11022245_52391187",
    "instruction": "...",
    "final_answer": "FINDINGS:\n...\n\nIMPRESSION:\n...",
    "payload": null
  }
]
```

## Concurrency Model

- `setup.sh`, the generator's per-task JPG download, and each container's
  entrypoint all flock on the same lock file
  (`assets/.locks/mimic-cxr-setup.lock` host-side; the same inode is
  visible inside containers via the bind mount at
  `/data/_src/jpg_root/.bootstrap.lock`).
- Mounts are `rw` so bootstrap can fill in missing files. In steady state
  nothing is written — the dataset behaves as read-only.
- Downloads are idempotent (`wget -c -N`); restarting a partial run
  resumes rather than re-fetching.

## Manual Replay Path

This is the canonical human replay path (workflow §4) used to distinguish
agent failures from task / environment / verifier failures. After the
generator has produced a specific patient task, a human can execute the
same workflow manually inside a fresh task container:

```bash
# 1. Build and start the task container (concurrency = 1 to get a shell).
cd tasks/mimic_report_gen/p10046166_s50051329/environment
docker compose up --detach --wait main
docker compose exec main bash

# --- inside the container ---

# 2. Inspect the agent-visible workspace.
ls /workspace                                # benchmark_tasks.json, submission.json, README.md
cat /workspace/benchmark_tasks.json | jq .

# 3. Inspect the materialized patient data.
ls /data/patient                             # manifest.json + timestamped folders
cat /data/patient/manifest.json | jq .
for f in /data/patient/*/report.txt; do
  echo "=== $f ==="
  cat "$f"
done

# 4. Inspect the target study's images (the target folder has NO report.txt).
ls /data/patient/$(jq -r '.studies[] | select(.is_target) | .folder' \
                   /data/patient/manifest.json)

# 5. Write a hand-crafted FINDINGS + IMPRESSION into submission.json,
#    using a JSON-aware tool (not sed / manual edits).
python - <<'PY'
import json, pathlib
path = pathlib.Path("/workspace/submission.json")
data = json.loads(path.read_text())
data[0]["final_answer"] = """FINDINGS:
No acute cardiopulmonary process. Stable cardiomediastinal silhouette.

IMPRESSION:
No acute cardiopulmonary findings."""
path.write_text(json.dumps(data, indent=2))
PY

# 6. Run the verifier.
bash /tests/test.sh
cat /logs/verifier/meta_results.json
cat /logs/verifier/reward.json
```

If step 6 produces a non-empty `reward.json` with the `chx_ref_*` and
`chx_pred_*` scalar fields populated and no `chexbert_error.txt`, the task
/ environment / verifier are all healthy; any real-agent failure should
then be investigated as an agent-execution or instruction-following bug.

## Validation Commands

These commands match the workflow §7 recommended checks. Run from the
repo root in order; later commands depend on earlier ones succeeding.

```bash
# 0. Install deps, activate venv.
uv sync --all-extras
source .venv/bin/activate

# 1. Download the two dataset-wide PhysioNet assets (idempotent).
export PN_USER=<physionet_username>
export PN_PASS=<physionet_password>
bash scripts/mimic_report_gen/setup.sh

# 2. Generate the Harbor task tree (+ per-task JPG bootstrap).
#    Default: every eligible patient. Use --sample-size N for a cap.
uv run python scripts/mimic_report_gen/generate_harbor_tasks.py \
  --output-root tasks/mimic_report_gen \
  --sample-size 5          # tiny set for validation; omit for full test split

# 3. Smoke-test benchmark-specific helpers and the aggregator math.
uv run pytest tests/test_mimic_report_gen_task.py -q

# 4. Run a single-trial Harbor job end-to-end. Point task_names at one of
#    the generated subtasks.
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run harbor run -c jobs/mimic_report_gen.yaml

# 5. Run a multi-model sweep and render the baseline table.
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_report_gen \
  --task-path tasks \
  --harness codex \
  --model gpt-5.3-codex \
  --model gpt-5.4 \
  --attempts 1 \
  --concurrency 15 \
  --reasoning-effort medium \
  --no-detailed \
  --metric-to-report avg_rouge_l \
  --metric-to-report chexbert_f1_14_micro_f1 \
  --artifact /workspace/submission.json \
  --output-root results/baselines/mimic_report_gen \
  --baselines-md paper/baselines.md
```

> **Note on concurrency.** Docker's default network-address pool caps at
> ~31 simultaneous bridge networks. Each Harbor trial creates one network,
> so `--concurrency` × number-of-models must stay below ~30 unless you
> expand `default-address-pools` in `/etc/docker/daemon.json`. The default
> used in `jobs/mimic_report_gen.yaml` is `n_concurrent_trials: 15` to
> leave headroom when running two models in parallel via the multitask
> launcher.

## References

- **MIMIC-CXR paper**: https://doi.org/10.1038/s41597-019-0322-0
- **MIMIC-CXR v2.1.0**: https://physionet.org/content/mimic-cxr/2.1.0/
- **MIMIC-CXR-JPG v2.1.0**: https://physionet.org/content/mimic-cxr-jpg/2.1.0/
- **CheXbert labeler**: https://arxiv.org/abs/2004.09167
- **Harbor docs**: See `CLAUDE.md` for Harbor framework details
- **Related-work note**: `design/related_work/mimic_cxr_report_generation.md`
