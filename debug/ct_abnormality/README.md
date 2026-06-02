# ct_abnormality — debug helpers

This benchmark packages the CT-RATE chest-CT abnormality task. Each of the 10
subtasks hands the agent one CT volume at `/workspace/data/scan.nii.gz` and a
short list of labels to evaluate at `/workspace/data/labels.txt`, and the
agent writes `<label>: yes/no` predictions to
`/workspace/submission/predictions.txt`. Reward is binary: 1.0 iff every
requested label is correct.

See `scripts/ct_abnormality/README.md` for the benchmark specification and
`tasks/ct_abnormality/<task_id>/instruction.md` for the agent-facing task
description.

## When to use this

When a Harbor run goes wrong, the benchmark addition workflow asks you to
distinguish four failure classes:

- **agent failure** — the task works manually but the agent didn't execute it
- **task / environment failure** — the documented workflow can't be replayed
  (e.g. HF token missing, volume cache gone, gold.json absent)
- **verifier failure** — the verifier rejects semantically correct predictions
- **debug-tooling drift** — Harbor and the task are fine, debug helpers are stale

The manual replay path here distinguishes among them.

## One-time setup

1. Accept the CT-RATE access agreement at
   <https://huggingface.co/datasets/ibrahimhamamci/CT-RATE> while signed in.
2. Add `HF_TOKEN="hf_..."` to the repo-root `.env` (gitignored). The per-task
   `bootstrap` service loads it via `env_file: ../../../../.env` in its
   `docker-compose.yaml`; the token is given to `bootstrap` only and never
   reaches `main`/the agent. (The optional host-side downloader in step 3 also
   accepts `~/.cache/huggingface/token` from `huggingface-cli login`.)
3. Pre-stage the 10 NIfTI volumes (~3.5 GB) into the host cache (optional):

       uv run python scripts/ct_abnormality/download_volumes.py

   With pre-staging, the per-task bootstrap container hits the cache and
   skips the network. Without pre-staging, each first-run task downloads
   its own volume from HF (~5–7 s per volume) under a global host-side
   `flock`. The cache directory (`scripts/ct_abnormality/assets/raw_cache/`)
   is gitignored.

## Task tree shape

Each task directory under `tasks/ct_abnormality/<volume_stem>/` (e.g.
`tasks/ct_abnormality/valid_670_a_1/`) has the standard layout, with one
twist: the docker-compose declares **two services** — `main` (the agent
runs here) and `bootstrap` (a one-shot data-staging container) — joined
by `depends_on: bootstrap: condition: service_completed_successfully`.
Harbor's `docker compose up --detach --wait` blocks bringing `main` up
until `bootstrap` exits 0, so by the time the agent execs into `main`
the volume is already at `/workspace/data/scan.nii.gz` (via a shared
`workspace-data` named volume) and `labels.txt` is staged. There are
no sentinel files in `/workspace/`; synchronization is purely at the
compose layer.

**Gold is derived at run time, not committed.** The bootstrap also downloads the
volume's radiology report and runs `gold_derivation.py` (the phrase-rule module
shipped into the image) to write `tests/gold.json` — bind-mounted from the host
`tasks/ct_abnormality/<stem>/tests/` dir, which is **gitignored**. Harbor mounts
that same host dir as `/tests` when it later runs the verifier. `main` never
mounts `tests/`, so the agent never sees the gold. If you need to inspect the
derived gold, look at `tests/gold.json` after a bootstrap run, or run
`gold_derivation.py --reports-csv <csv> --volume <name>.nii.gz --out-gold ... --out-labels ...`
directly.

## Running a manual replay

Each task is a self-contained docker-compose project under
`tasks/ct_abnormality/<volume_stem>/environment/`. Use the repo-wide
debug helpers — they already understand the per-task docker-compose
layout:

    bash debug/up-task-env.sh tasks/ct_abnormality/valid_670_a_1
    bash debug/exec-task-shell.sh tasks/ct_abnormality/valid_670_a_1

    # Inside the container, sanity-check that bootstrap completed:
    #   ls -lh /workspace/data/scan.nii.gz   # real file (staged by bootstrap)
    #   cat /workspace/data/labels.txt       # task-specific label list
    # Then write a hand-crafted submission for the verifier:
    #   mkdir -p /workspace/submission
    #   cat > /workspace/submission/predictions.txt <<EOF
    #   Cardiomegaly: no
    #   Pericardial effusion: no
    #   Lymphadenopathy: no
    #   Lung nodule: no
    #   EOF

    bash debug/run-task-verifier.sh tasks/ct_abnormality/valid_670_a_1
    bash debug/down-task-env.sh tasks/ct_abnormality/valid_670_a_1

If you want to re-run *just* the bootstrap step (without bringing up
main), use `docker compose run --rm bootstrap` from the task's
`environment/` dir. The bootstrap exits 0 on success and prints
"[bootstrap] done — main can start".

The verifier writes `metrics.json` and `reward.json` under `/logs/verifier/`.
`reward.json` contains the binary `reward` (0.0 or 1.0), per-volume
`accuracy`, `n_correct`, `n_retained`, and `per_label[...]` with each
prediction and gold value.

`reward.txt` is deliberately not written — Harbor reads it first when
present, which would mask the rich per-trial reward.json payload.

## Sanity-check the verifier end-to-end

The verifier is purely string-matching on label names; it does not load the
volume. Reproduce expected behavior with the unit tests:

    uv run pytest tests/test_ct_abnormality_evaluator.py -v

The tests cover: perfect predictions → 1.0; one mistake → 0.0;
case-insensitive label match; comment / blank-line tolerance; numeric and
synonym tokens; missing submission → 0.0 + verifier_error.txt; missing label
in submission counted wrong; unknown labels in submission ignored.

## Failure-class triage

If a Harbor run fails:

1. **Inspect the Harbor run result first.** If `reward.json` is missing or
   malformed, jump to step 5 (verifier failure). If `reward.json` exists with
   `reward = 0.0` and `n_retained > 0` and `n_correct = 0`, the agent submitted
   wrong answers for every label — likely an instruction-following issue. If
   `n_correct = n_retained - 1`, the agent missed exactly one — interesting,
   inspect which label.
2. **Bootstrap-service failure.** If `predictions.txt` is missing or the
   agent's log suggests it ran before `/workspace/data/scan.nii.gz`
   existed, that should not happen under the new compose pattern: Harbor
   uses `docker compose up --detach --wait`, which blocks until the
   `bootstrap` service exits cleanly. Inspect bootstrap's exit code and
   logs with `docker compose logs bootstrap` (from the per-task
   `environment/` directory). If bootstrap exited non-zero, the most
   likely cause is HF auth (next item).
3. **HF token problem.** If the bootstrap service exits early with the
   message "no Hugging Face token: HF_TOKEN is empty", the token is missing
   from `.env` or compose didn't load it. Check
   `tasks/ct_abnormality/<volume_stem>/environment/docker-compose.yaml`
   for the `env_file: ../../../../.env` entry and ensure the repo-root
   `.env` defines `HF_TOKEN=hf_...`.
4. **Cache miss + slow CDN.** Concurrent containers all racing to download
   are serialized by a global flock over `/data/_cache/.bootstrap.lock`,
   so this should not produce thrashing. If you see all containers stuck
   on the same volume for many minutes, check HF Hub status.
5. **Verifier failure.** If the manual replay above produces sane predictions
   but the verifier crashes or returns 0, fix
   `scripts/ct_abnormality/harbor_evaluator.py` and re-run the unit tests.
6. **Agent failure.** If the manual replay scores high but the Harbor agent
   run scored low, treat it as an agent execution / instruction following
   issue and inspect the trial transcript.

## Expected baseline

(Populated after Milestone 9 of `.agent/plans/ct_abnormality.md`.)

A working environment + verifier should produce non-zero `success` from at
least the easiest task — `task_1` (`valid_670_a_1.nii.gz`) is a normal scan
with four explicit-negative labels (Cardiomegaly, Pericardial effusion,
Lymphadenopathy, Lung nodule, all gold = 0). Submitting `no` for every label
should score 1.0. If a model cannot pass `task_1`, suspect a plumbing bug
before assuming the model can't do the task.
