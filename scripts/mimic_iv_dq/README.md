# MIMIC-IV-DQ — Synthetic Data-Quality Detection

This directory contains the Harbor-first integration for the
`mimic_iv_dq` benchmark. Each task hands the agent a corrupted EHR
dataset (a 100-patient MIMIC-IV-demo subset, source name hidden) under
`/workspace/data/csv/` and asks it to flag rows that contain
deliberately-injected data-quality errors. F1 is computed against a
hidden ground-truth label set.

## Canonical Source and Canonical Runner

- Canonical upstream source: PhysioNet `mimic-iv-demo` v2.2 (public,
  no credentials)
- Canonical Harbor task generator: `scripts/mimic_iv_dq/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/mimic_iv_dq/`
- Per-benchmark asset cache: `scripts/mimic_iv_dq/assets/` (the
  `raw_cache/`, `labels/`, and `_task_slices/` subdirectories are
  gitignored — `task_configs.yaml` is the only committed asset)
- Verifier-side metric aggregator: `scripts/mimic_iv_dq/aggregate_metric.py`

## Benchmark Shape

This benchmark evaluates whether an agent can:

1. inspect eight EHR tables at `/workspace/data/csv/` (`patients`,
   `admissions`, `labevents`, `prescriptions`, `d_labitems`, `icustays`,
   `chartevents`, `d_items`) loaded into pandas / duckdb / sqlite as
   the agent prefers
2. detect rows belonging to one of three error-family categories named in
   the task's `instruction.md`: **impossible values** (range-extreme /
   decimal-shift / unit-confusion / valueuom-mismatch sub-types),
   **conflicting / duplicate records** (in-table conflict pairs with
   natural-range fresh PKs and jittered charttimes; cross-table
   lab↔chart conflicts whose synthetic chartevents row uses a real
   `icustays.stay_id`), **demographic contradictions** (`gender_via_patients_flip`
   plus expanded sex-marker-drug + sex-specific-lab evidence,
   `gender_via_prescription_swap` writing an opposite-sex marker drug onto
   a neutral prescription, `gender_via_ref_range_swap` overwriting a
   sex-specific lab's `ref_range_lower/upper` with the opposite-sex
   canonical band, and `age_via_patients_change` for geriatric-drug
   carriers)
3. emit a CSV at `/workspace/submission/flagged_rows.csv` with at least
   `(table, _row_id)` columns

Four tasks ship: one per error family plus a fourth combined task that
mixes all three. (A `temporal_violation` family was prototyped but
removed because the pristine demo contains real-world temporal anomalies
— charttime/storetime ordering, home-meds preceding admission — that
can't be cleanly distinguished from injected violations.)

The verifier computes cluster-level recall (a multi-row cluster is
caught when the agent flags any row in it), row-level precision, and
F1 — F1 is the reward Harbor reads via per-trial `reward.json`. For
demographic_conflict the cluster is intentionally wide: the mutated row
plus *every* row in any table that legitimately reveals the
contradiction (sex-marker drugs, sex-specific labs, opposite-sex
ref-range labs, geriatric drugs).

## Canonical Workflow

> **No credentials required.** MIMIC-IV-demo is publicly accessible on
> PhysioNet. The Docker build downloads the required tables on the fly.

```bash
# 0) Codex login (the agent runtime needs ~/.codex/auth.json on the host)
codex login status

# 1) (Optional) Pre-populate the pristine-demo cache once so the
#    generator can rebuild labels offline.
uv run python -c "
from pathlib import Path; import sys
sys.path.insert(0, 'scripts/mimic_iv_dq')
from stage_data import _download_all
_download_all(Path('scripts/mimic_iv_dq/assets/raw_cache'))"

# 2) Generate (or regenerate) the four Harbor task subdirectories. The
#    --regenerate-labels flag re-runs the corruption pipeline locally
#    and refreshes labels.csv. Skip --regenerate-labels to reuse the
#    committed labels in tasks/mimic_iv_dq/<task>/tests/labels.csv.
uv run python scripts/mimic_iv_dq/generate_harbor_tasks.py \
  --output-root tasks/mimic_iv_dq \
  --regenerate-labels

# 3) Run the Harbor job. You can skip steps 1 and 2 — the Dockerfile
#    downloads the pristine demo at image build time, applies the
#    corruption recipe, and verifies against the committed labels.csv.
uv run harbor run -c jobs/mimic_iv_dq.yaml
```

To regenerate just one or two tasks (faster iteration):

```bash
uv run python scripts/mimic_iv_dq/generate_harbor_tasks.py \
  --output-root tasks/mimic_iv_dq \
  --regenerate-labels \
  --task-ids task_combined,task_impossible_value
```

## Multi-Model Baselines

To benchmark several models against all 4 tasks with N trials each and
a rendered markdown report, use the shared
`run_harbor_baselines_multitask.py`. Both the `codex` and `copilot-cli`
harnesses are supported; results from both can be aggregated into a
single `## mimic_iv_dq` section in `paper/baselines.md` by re-rendering
with all run dirs at once (`--mode render --run-dir …`).

Codex harness:

```bash
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

uv run python scripts/run_harbor_baselines_multitask.py \
    --task-name mimic_iv_dq \
    --task-path tasks \
    --harness codex \
    --model gpt-5.3-codex \
    --model gpt-5.4 \
    --model gpt-5.5 \
    --attempts 3 \
    --concurrency 2 \
    --metrics-script scripts/mimic_iv_dq/aggregate_metric.py \
    --metric-to-report f1 \
    --metric-to-report recall \
    --metric-to-report precision \
    --baselines-md paper/baselines.md
```

Copilot-cli harness (Claude + GPT models via GitHub Copilot):

```bash
export GH_TOKEN="$(tr -d '[:space:]' < ~/.github_credentials/github_pat)"

uv run python scripts/run_harbor_baselines_multitask.py \
    --task-name mimic_iv_dq \
    --task-path tasks \
    --harness copilot-cli \
    --model claude-opus-4.6 \
    --model claude-sonnet-4.6 \
    --model gpt-5.4 \
    --attempts 3 \
    --concurrency 2 \
    --metrics-script scripts/mimic_iv_dq/aggregate_metric.py \
    --metric-to-report f1 \
    --metric-to-report recall \
    --metric-to-report precision \
    --baselines-md paper/baselines.md
```

Each invocation runs **N models × 4 subtasks × 3 attempts = 12N
trials**. The launcher reads each trial's `verifier/reward.json`
directly so per-trial `f1` / `recall` / `precision` populate both:

- **Aggregate Summary table** — one row per (harness, model, reasoning):
  reports each metric as mean ± sample stdev across the 4 × 3 = 12
  trials per (harness, model) combo.
- **Detailed Attempts table** — one row per trial with per-trial
  `f1`, `recall`, `precision`, plus run/trial dirs for tracing back to
  raw Harbor output.

`paper/baselines.md` updates use a per-`task_name` upsert
(`upsert_task_section` in the launcher), so re-running for the same
`--task-name` replaces the entire `## mimic_iv_dq` section. To preserve
both codex and copilot results, render once with all run dirs together
in `--mode render`.

Pass `--no-detailed` to suppress the per-trial section. To also surface
the aggregator's pooled (per-family / per-subtype) recall, add
`--metric-to-report mean_f1 --metric-to-report mean_recall
--metric-to-report mean_precision` — those keys come from the
`aggregate_metric.py` uv-script output and appear as aggregate-only
columns (no per-trial stdev).

## Anti-Cheat

The benchmark relies on **source-name obfuscation** to deter the trivial
"wget the pristine source and diff" attack:

- No agent-visible artifact mentions MIMIC-IV-demo, MIMIC, PhysioNet, or
  the source URL.
- `instruction.md` refers to the data as "an EHR dataset" and explicitly
  forbids the agent from using the internet to look up reference values
  or attempt to re-download a "pristine" copy of the data.

Schema-level fingerprinting (well-known table/column names, MIMIC-specific
itemids) is *not* obscured because that would break the legitimate EHR
prior knowledge an agent should be able to apply.

A container-level egress block (modifying `/etc/hosts` to redirect
PhysioNet hostnames to `127.0.0.1`) is **not** currently active:
`/etc/hosts` is read-only during `docker build` so it can't be changed
at image-build time. A follow-up could add a runtime entrypoint script
that writes to `/etc/hosts` at container startup if a stronger defense
is needed.

### Shortcut closures (injector-side)

Agents found multiple synthetic-tell shortcuts in early iterations.
The injectors now defend against them so detection requires legitimate
EHR reasoning rather than artifact-grepping:

- **value ↔ valuenum sync**: `_apply_range_extreme`, `_apply_decimal_shift`,
  `_apply_unit_confusion` rewrite the parallel `value` string column
  alongside `valuenum` so the agent can't grep for rows where the two
  columns disagree.
- **Sentinel sampling**: range-extreme replacements are sampled from a
  per-itemid implausible band (`RANGE_VIOLATIONS[...][3:5]`), not a
  single hard-coded value like `999.9`.
- **Float-artifact rounding**: `unit_confusion`, `in_table_conflict`
  duplicates, and `cross_table_conflict` synthetic rows all round to
  per-itemid `DEVICE_PRECISION` so values don't read like
  `6.840000000000001`.
- **Natural-range fresh PKs**: `in_table_conflict` duplicates get a fresh
  `labevent_id` / `pharmacy_id` sampled from gaps within the existing
  range (via `_fresh_pk_in_range`) — never the 10⁹+ band that an early
  prototype used.
- **Real FK lookup**: `cross_table_conflict`'s synthetic chartevents row
  uses the patient's actual `icustays.stay_id` (matched by charttime
  ∈ [intime, outtime] window) so the row passes an FK-against-icustays
  check.
- **Charttime jitter**: in_table_conflict duplicates carry ±5min
  charttime offset so a naive exact-charttime group-by misses them.
- **Varied multipliers**: in_table_conflict uses `rng.uniform(1.10, 1.50)`
  per-row, not a static ×1.05.
- **Canonical opposite-sex band swap**: `gender_via_ref_range_swap`
  overwrites a sex-specific lab's `ref_range_lower/upper` with the
  *opposite-sex* canonical band (`SEX_REF_RANGES`), not a relative
  shift — making the demographic contradiction sharp and detectable
  via a single JOIN.

## Build-Time Verification

Each generated `Dockerfile` runs `_stage_data.py --verify-against` against
the committed `labels.csv`. If the freshly-applied corruption disagrees
with the committed labels, the image fails to build with a clear error
message — this catches injector drift early, well before any agent run.

## Harbor Artifacts

The Harbor job at `jobs/mimic_iv_dq.yaml` retains these artifacts after
each run for error analysis:

- `/workspace/submission/flagged_rows.csv` — the agent's flagged rows
- `/logs/verifier/metrics.json` — full per-task metrics (F1, recall,
  precision, per-family / per-subtype recall, cluster counts, turn count)
- `/logs/verifier/reward.json` — the structured reward Harbor pools
  through the aggregator

## Manual Replay

For the human replay path used to distinguish agent failures from
task / environment / verifier failures, see
`debug/mimic_iv_dq/README.md`.

## References

- **MIMIC-IV-demo v2.2**: https://physionet.org/content/mimiciv-demo/2.2/
- **Weiskopf & Weng (2013) — EHR data-quality dimensions**:
  https://pubmed.ncbi.nlm.nih.gov/22733976/
- **Related-work note**: `design/related_work/mimic_iv_dq_synthetic.md`
- **ExecPlan**: `.agent/plans/mimic_iv_dq.md`
