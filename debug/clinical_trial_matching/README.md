# clinical_trial_matching — debug helpers

This benchmark packages the TREC Clinical Trials 2021 patient-to-trial
ranking task. Each of the 10 subtasks hands the agent one synthetic
admission note plus a topic-specific judged-pool corpus of ~400–600
clinical-trial XMLs, and the agent writes a ranked NCT list to
`/workspace/submission/ranked_trials.txt`. Reward is **NDCG@10** with
linear gain over physician qrels (eligible=2 / excluded=1 / non-relevant=0);
it is reduced to a binary 0/1 in `reward.json` for Harbor's pass/fail
counting (1 iff NDCG@10 == 1.0).

See `scripts/clinical_trial_matching/README.md` for the benchmark
specification and `tasks/clinical_trial_matching/<task_id>/instruction.md`
for the agent-facing task description.

## When to use this

When a Harbor run goes wrong, the benchmark addition workflow asks you to
distinguish four failure classes:

- **agent failure** — the task works manually but the agent didn't execute it
- **task / environment failure** — the documented workflow can't be replayed
  (e.g. cold-cache download race, missing trial XMLs, qrels mismatch)
- **verifier failure** — the verifier rejects a semantically correct ranking
- **debug-tooling drift** — Harbor + task are fine, debug helpers are stale

The manual replay path here distinguishes among them.

## One-time setup

The replay reuses the host-side per-trial cache at
`scripts/clinical_trial_matching/assets/raw_cache/`. That directory is
gitignored. Running the task generator with `--skip-prefetch` is fine —
each task's `entrypoint.sh` will fetch the trials it needs into the cache
on first run, holding a global `flock` so concurrent containers don't
hammer trec-cds.org. To pre-populate the cache once for offline-fast
debugging:

    uv run python scripts/clinical_trial_matching/generate_harbor_tasks.py

(omit `--skip-prefetch`). Expect the first cold pass to take ~5 min/topic
because all per-topic NCTs are pulled via HTTP range requests across the
five upstream zip parts.

## Running a manual replay

Each task is a self-contained docker-compose project under
`tasks/clinical_trial_matching/<task_id>/environment/`. Use the
repo-wide debug helpers (`debug/up-task-env.sh`,
`debug/run-task-manually.sh`, `debug/run-task-verifier.sh`,
`debug/down-task-env.sh`) — they already understand the per-task
docker-compose layout.

Sketch:

    # Build + start one task's environment
    bash debug/up-task-env.sh tasks/clinical_trial_matching/task_27

    # Open a shell, inspect /workspace/data/topic.txt and /workspace/data/trials/
    bash debug/exec-task-shell.sh tasks/clinical_trial_matching/task_27

    # Inside the container, sanity-check that bootstrap finished:
    #   ls /workspace/.bootstrap_done   # should exist before agent runs
    #   ls /workspace/data/trials | wc -l   # should be 400-600 NCT_*.xml
    # Then write a hand-crafted ranked submission to verify scoring:
    #   cat > /workspace/submission/ranked_trials.txt <<'EOF'
    #   NCT_perfect_match
    #   NCT_second_match
    #   ...
    #   EOF

    # Run the verifier alone (no agent)
    bash debug/run-task-verifier.sh tasks/clinical_trial_matching/task_27

    # Tear down
    bash debug/down-task-env.sh tasks/clinical_trial_matching/task_27

The verifier writes `metrics.json` and `reward.json` under
`/logs/verifier/`. Inspect both:

- `reward.json` is what Harbor reads: `reward` is binary (0/1),
  `ndcg_at_10` is the underlying graded score, plus diagnostic counts
  (TP / FP-by-cause / FN, NDCG@10, P@10, R@10, F1, P, R).
- `metrics.json` is the rich diagnostic payload (same keys as
  `reward.json`, no `reward` field collapse).

`reward.txt` is deliberately not written — Harbor reads it first when
present, which would mask the rich per-trial reward.json payload.

## Sanity-check the ranking metric end-to-end

A common confusion is "my ranking has the right NCTs but my score is
low." Reproduce expected behavior with the unit tests:

    uv run pytest tests/test_clinical_trial_matching_evaluator.py -v

The tests cover the five interesting cases the verifier must handle
correctly: ideal order → 1.0, mis-ordering → < 1.0, eligibles past
rank 10 → 0 contribution, unjudged predictions → 0 gain (but counted
as FP in F1), and binary reward iff NDCG@10 == 1.0.

## Failure-class triage

If a Harbor run fails:

1. **Inspect the Harbor run result first.** If `reward.json` is missing
   or malformed, jump to step 4 (verifier failure). If `reward.json`
   exists with `ndcg_at_10` = 0.0 *and* `n_predicted` = 0, the agent
   never wrote a submission — almost always either a bootstrap race
   (agent started before `/workspace/.bootstrap_done` existed) or an
   instruction-following failure. Check `agent/trial.log`.
2. **Bootstrap race.** If `n_ranked` = 0 across many trials,
   confirm the entrypoint sentinel works: inside the container,
   `/workspace/.bootstrap_required` should be created up-front and
   `/workspace/.bootstrap_done` only after `chmod -R a-w` finishes.
   Codex's setup hook in
   `src/medcli/agents/harbor/installed/codex.py` polls for
   `bootstrap_done`; claude-code uses the same sentinel via
   `claude_code.py`.
3. **Cold-cache server throttling.** If multiple concurrent containers
   timed out simultaneously on the first run for a topic, the entrypoint's
   global `flock` was bypassed (e.g. cache dir was deleted mid-run).
   Re-run with concurrency 1 for the cold pass, or pre-populate the
   cache as in "One-time setup" above.
4. **Verifier failure.** If the manual replay above produces a sane
   `ranked_trials.txt` but the verifier crashes or returns 0, fix
   `scripts/clinical_trial_matching/harbor_evaluator.py` and re-run
   the unit tests.
5. **Agent failure.** If the manual replay scores high but the Harbor
   agent run scored low, treat it as an agent execution / instruction
   following issue and inspect the trial transcript.

## Expected baseline

NDCG@10 for current frontier models on the 10-task suite (1 attempt):

| model | NDCG@10 | success | F1 (full) |
|---|---|---|---|
| gpt-5.5 (codex) | 0.928 | 4/10 | 0.402 |
| claude-opus-4-7 | 0.883 | 2/10 | 0.542 |
| gpt-5.4 (codex) | 0.849 | 3/10 | 0.197 |
| claude-sonnet-4-6 | 0.817 | 1/10 | 0.423 |
| gpt-5.3-codex | 0.586 | 0/10 | 0.109 |

A working environment + verifier should produce non-zero NDCG@10 even
for trivial baselines (e.g. submitting the full judged-pool list in
arbitrary order yields NDCG@10 strictly above 0 because some grade-1
or grade-2 entries land in the top 10 by chance). NDCG@10 = 0.0 across
many trials almost always indicates a bootstrap race or empty
submission, not a poor ranking. See `paper/baselines.md` for the
canonical results table.
