# ehr_data_quality — debug helpers

This benchmark packages a synthetic data-quality detection task over a
corrupted MIMIC-IV-demo subset. See `scripts/ehr_data_quality/README.md` for the
benchmark specification and `tasks/ehr_data_quality/<task_id>/instruction.md` for
the agent-facing task description.

## When to use this

When a Harbor run goes wrong, the benchmark addition workflow asks you to
distinguish four failure classes:

- **agent failure** — the task works manually but the agent didn't execute it
- **task / environment failure** — the documented workflow can't be replayed
- **verifier failure** — the verifier rejects semantically correct output
- **debug-tooling drift** — Harbor + task are fine, debug helpers are stale

The `manual_replay.sh` here distinguishes among them.

## One-time setup

The replay script reads pristine MIMIC-IV-demo CSVs from
`scripts/ehr_data_quality/assets/raw_cache/`. That directory is gitignored.
Pre-populate it once:

    uv run python -c "
    from pathlib import Path; import sys
    sys.path.insert(0, 'scripts/ehr_data_quality')
    from stage_data import _download_all
    _download_all(Path('scripts/ehr_data_quality/assets/raw_cache'))"

## Running a manual replay

From the repo root:

    bash debug/ehr_data_quality/manual_replay.sh                          # all 4 tasks
    bash debug/ehr_data_quality/manual_replay.sh task_impossible_value    # one task

For each task the script:

1. Stages corrupted CSVs into `/tmp/dq_replay/<task_id>/data/` using exactly
   the same `stage_data.py` invocation the Dockerfile runs at image build
   time, including `--verify-against` against the committed `labels.csv`.
2. Runs `scripts/ehr_data_quality/reference_solver.py` against those CSVs and
   writes `flagged_rows.csv`.
3. Runs the harbor verifier and prints `f1`, `recall`, `precision`,
   `n_flagged_rows`, `n_useful_flagged_rows`, and the cluster catch ratio.

Logs land at `/tmp/dq_replay/<task_id>/{stage,solver}.log` and
`/tmp/dq_replay/<task_id>/logs/verifier/{reward.json,metrics.json}`.
(`reward.txt` is deliberately not written — Harbor reads it first when
present, which would mask the rich per-trial reward.json payload.)

## Expected baseline

The reference solver is a deterministic heuristic that runs every per-family
detector unconditionally. It demonstrates the task is solvable (high cluster
recall) but flags many real-but-not-injected anomalies, so its precision is
intentionally low. Approximate baseline:

| Task | Recall (clusters) | Precision (rows) | F1 |
|---|---|---|---|
| `task_impossible_value` | ~0.40 | ~0.01 | ~0.03 |
| `task_inconsistency` | 1.00 | ~0.06 | ~0.12 |
| `task_demographic_conflict` | 1.00 | ~0.01 | ~0.03 |
| `task_combined` | ~0.85 | ~0.05 | ~0.09 |

A capable agent that uses the per-task category hints in `instruction.md`
to *filter* anomaly candidates should achieve substantially higher
precision, and so substantially higher F1, than this floor. See
`paper/baselines.md` for current model results.

> The `temporal_violation` family was removed from the benchmark
> because the pristine MIMIC-IV-demo contains real-world temporal
> anomalies (charttime/storetime ordering, home-meds preceding
> admission) that can't be cleanly distinguished from injected
> violations.

## Failure-class triage

If a Harbor run fails:

1. Inspect the Harbor run result and logs first.
2. `bash debug/ehr_data_quality/manual_replay.sh <task_id>`. If staging fails,
   that's a **task failure**. If staging succeeds but `_verify_against`
   raises `SystemExit`, the committed `labels.csv` and the build-time
   injection drifted apart — regenerate via
   `uv run python scripts/ehr_data_quality/generate_harbor_tasks.py
    --regenerate-labels` and commit the refreshed labels.
3. If the verifier crashes on the reference-solver output, it's a **verifier
   failure** — fix `harbor_evaluator.py`.
4. If everything passes manually but Harbor failed, treat it as an **agent
   failure** and inspect the agent transcript.
