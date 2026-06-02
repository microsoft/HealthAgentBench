# Human Review Checklist

This document is the canonical checklist a human runs before declaring a
MedCLI task ready to merge. Work through it starting from a **freshly
pulled repo in a clean directory on a clean machine** — that's the only
context in which the "reproducibility" guarantees mean anything.

The checklist has three phases per task, plus one final pass across the
whole suite:

- **A. Task generation** — what the task ships looks correct on disk.
- **B. Harbor run** — the task actually runs end-to-end via Harbor.
- **C. Persistence & PR** — results are archived and the change is
  reviewable.

Then once every task is integrated, the **suite-level** section at the
bottom confirms the cross-task wiring works.

---

## A. Task generation

### A1. Task identity is generic and leak-free

- [ ] The task name does not reveal the source dataset or upstream
      benchmark name.

### A2. README contains everything needed to re-run

- [ ] `scripts/<task>/README.md` documents data setup, authentication, generation command, and runtime instructions.
- [ ] If credentials are required (PhysioNet, Redivis, Hugging Face, etc.), they are also listed in the repo-level `README.md` /
      `.env` schema so a new user can find them.

### A3. Agent instruction is minimal and includes the standard guardrails

- [ ] `tasks/<task>/<subtask>/instruction.md` is as short as possible —
      goal + I/O contract, not strategy.
- [ ] States the **1-hour completion budget** explicitly.
- [ ] Includes the canonical anti-cheat sentence verbatim:
      *"You should not cheat and you should not directly look up for
      the end solutions from the internet."*

### A4. No test leakage to the agent

- [ ] No task name, original IDs, or dataset name visible in any path
      the agent can reach.
- [ ] `tests/` directory is **not** copied into the agent's container
      image. Gold labels and verifier code are mounted only at
      scoring time.
- [ ] Anything bind-mounted into the bootstrap service (gold labels,
      task config) is **not** bind-mounted into the main service.

### A5. No hard-coded absolute paths

- [ ] Search `scripts/<task>/` and `tasks/<task>/` for
      `/home/...`, `/Users/...`, `/mnt/...`. Only container-internal
      absolute paths (`/workspace/`, `/data/`, `/tests/`, `/logs/`)
      are acceptable.

### A6. No proprietary data checked into git

- [ ] Raw upstream data lives under `scripts/<task>/assets/` and is
      gitignored.
- [ ] No PHI, no credentialed files, no test labels under
      `tasks/<task>/` or are gitignored. (Cached labels at `assets/labels/<task>.csv`
      are OK if they're derived from public/synthetic data.)

### A7. On-the-fly data download

- [ ] Remove or rename `scripts/<task>/assets/` and confirm a clean
      `harbor run` still works — the per-task bootstrap container
      should fetch the data from upstream on first run.
- [ ] Two-service docker-compose pattern (bootstrap + main with
      credential isolation) — reference `tasks/xray_report_correction/` or
      `tasks/ehr_data_quality/`.

### A8. Evaluation script emits the standard metrics

- [ ] Per-trial `reward.json` is flat scalars and includes at least
      `{reward/pass_rate, n_tasks, n_pass/n_correct}`.
- [ ] `scripts/<task>/aggregate_metric.py` pools per-trial rewards
      into job-level **success** (count of passing trials) and
      **reward** or **pass_rate** (count of passing trials/total trials). Reference `xray_report_correction`.

---

## B. Harbor run

### B1. Single-task smoke

- [ ] `uv run harbor run -c jobs/<task>.yaml` completes for one model
      end-to-end (bootstrap → agent → verifier → reward.json) with removed or renamed `scripts/<task>/assets/` to test on-the-fly boostrapping.

### B2. Multi-model multitask sweep

Run `scripts/run_harbor_baselines_multitask.py` with all models (codex gpt-5.5, gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, claude code opus-4-8, opus-4-7, opus-4-6, sonnet-4-6) with xhigh reasoning effort and `--attempts 3`. Before launching:

- [ ] Docker address pool is healthy (`docker network ls` not near the
      ~31-bridge ceiling).
- [ ] No leftover containers from prior runs
      (`docker ps` empty).

Sweep command should include:

- [ ] `--baselines-md paper/baselines.md` so results render into the
      paper table.
- [ ] `--artifact /workspace/submission/<output>` to preserve agent
      predictions for inspection. (Only files under `/workspace/`
      need `--artifact` to be copied out. `agent_result.cost_usd` +
      token counts are written into every `<trial>/result.json`
      regardless, and `<trial>/verifier/{reward,metrics}.json` are
      preserved by Harbor automatically.)
- [ ] At minimum: success, mean reward, and **USD cost** columns
      surface in `paper/baselines.md`. The launcher pulls cost from
      `agent_result.cost_usd` automatically.
- [ ] `--disable-web-browser` is passed when the benchmark's gold
      answer (or a recognisable phrase from it) is reachable via a
      public mirror or general web search. The flag defaults to OFF
      so internet stays available; pass it explicitly for tasks like
      `xray_report_correction`.

### B3. Result-directory sanity

- [ ] Failed trials (Docker errors, timeouts) are counted as
      **no-pass** in the final success and reward — not silently
      skipped. The aggregator should synthesize a zero-reward row
      for any trial with `exception.txt` but no `reward.json`.
- [ ] No failures attributable to environment setup (bootstrap
      errors, network exhaustion, etc.) — those would invalidate
      the agent comparison.
- [ ] Spot-check agent trajectories (`agent/codex.txt`,
      `agent/trajectory.json`) to confirm the model is not cheating
      (no internet lookups for gold answers, no path traversal to
      `/tests/`).
- [ ] No task is passed by all agents for all three attempts. If the task is too easy we should discard it. 

---

## C. Persistence & PR

### C1. Archive results to blob storage

`rsync` local result dirs to
`/mnt/hanoverdev/scratch/qianchuliu/medcli/results/<task>` with these
exclusions to keep the upload size sane:

```bash
rsync -av \
  --exclude="agent/.tmp/" \
  --exclude="agent/cache/" \
  --exclude="agent/setup/" \
  --exclude="agent/shell_snapshots/" \
  --exclude="agent/memories/" \
  --exclude="agent/tmp/" \
  --exclude="agent/installation_id" \
  --exclude="agent/models_cache.json" \
  --exclude="agent/state_*.sqlite*" \
  --exclude="agent/logs_*.sqlite*" \
  results/harbor/<task>/ \
  /mnt/hanoverdev/scratch/qianchuliu/medcli/results/<task>/
```

Also make sure these mnt mounted result directories are rendered in paper/baselines.md

### C2. Final review before PR

- [ ] All checks above are green.
- [ ] `paper/baselines.md` row exists for the task with mnt mounted directories.
- [ ] `tasks/README.md`, `design/tasks.md`, and
      `paper/benchmarks.md` reference the task and all documents are updated. 
- [ ] No untracked artifacts that should be ignored
      (`git status` is clean except for intended additions).
- [ ] Review the PR change files and add a PR description markdown

---

## Suite-level (once every task is integrated)

1. **All-task job YAML.** Create a single job config that can run with
   `uv harbor run` across every integrated task. Smoke it for one
   attempt per task and confirm a single pass-rate table comes out.

2. **Top-level README is complete.** `MedCLI/README.md` documents:
   - How to re-run the all-task sweep.
   - How to re-run a single task.
   - All required credentials and their setup paths.
   - Pointers to per-task READMEs (`scripts/<task>/README.md`).

3. Check all tests are passed for all tasks. 