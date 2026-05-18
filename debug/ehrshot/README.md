# EHRSHOT Debug

This directory documents the EHRSHOT-specific debug flow built on top of the
generic Harbor debug workflow in `debug/README.md`. EHRSHOT does not currently
ship benchmark-specific wrapper scripts — the generic helpers under `debug/`
work as-is once the gated bundle has been downloaded on the host (or you let
the container bootstrap fetch it).

## Prerequisites

EHRSHOT data is gated behind a Redivis access agreement. The host needs a
Redivis API token at `~/.redivis/api_token` before any task environment can
build or run. See `scripts/ehrshot/README.md` for the access-request and
token-setup steps.

## Recommended Flow

Pick one task (e.g. `lab_anemia`) and use the generic helpers:

```bash
# Build the per-task image (also re-bakes stage_data.py + evaluate.py)
bash debug/build-task-env.sh tasks/ehrshot/lab_anemia

# Start the compose stack. The bootstrap service downloads the bundle on
# cache miss, slices events, partitions labels by split, and writes
# train/val/test artifacts to the agent-visible workspace volume. The
# `main` service starts only after bootstrap exits cleanly.
bash debug/up-task-env.sh tasks/ehrshot/lab_anemia

# Open a shell inside the running `main` container
bash debug/exec-task-shell.sh tasks/ehrshot/lab_anemia
```

Inside the container, the agent-visible inputs live under `/workspace/data/`:

- `train_labels.csv`, `val_labels.csv` — labeled train/val rows.
- `test_examples.csv` — unlabeled test rows. The agent must write
  `/workspace/submission/predictions.csv` matching `(patient_id,
  prediction_time)` on these rows.
- `events.csv` — the per-task leak-proof slice of the longitudinal event
  log. For test patients, only rows with `start < prediction_time` are
  kept and any future `end` is blanked. The agent should still enforce
  `start < T` for each prediction row when building features.
- `splits/person_id_map.csv` — patient → split mapping (cross-check only).

## Manual Replay Path

The canonical manual replay path mirrors what an agent would do:

```bash
# Inside the running `main` container
cd /workspace
python -c "
import pandas as pd
te = pd.read_csv('data/test_examples.csv')
te['probability'] = 0.5
te.to_csv('submission/predictions.csv', index=False)
"
```

Then run the verifier from the host:

```bash
bash debug/run-task-verifier.sh tasks/ehrshot/lab_anemia
```

This produces `verifier/reward.json` with `reward`, `success`, `auroc`,
`auprc`, `brier`, `n_test`, and `baseline_auroc`. The baseline AUROC is
read from `tasks/ehrshot/lab_anemia/tests/baseline.json`; if your test
labels were freshly generated, `success` requires `auroc >= baseline_auroc`.

## Common Issues

- **Bootstrap fails with a 401 from Redivis.** The token in
  `~/.redivis/api_token` is missing or stale. Refresh it via the Redivis UI
  and re-run `bash debug/up-task-env.sh`.
- **`test_labels.csv` not found during verifier.** The bootstrap service
  writes `test_labels.csv` to the host-side `tests/` bind-mount, not to
  the agent workspace. If the file is missing, the bootstrap container
  failed mid-way — check `docker compose logs bootstrap`.
- **AUROC is suspiciously close to 1.0 on `guo_los`.** Inspect the events
  slice for any rows with non-blank `end` timestamps on test patients; if
  blanking is broken, the slicer leaks the future discharge time. The
  slicer is in `scripts/ehrshot/stage_data.py:slice_events_for_task`.
