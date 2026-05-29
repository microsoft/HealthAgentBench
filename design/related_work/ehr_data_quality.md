# MIMIC-IV-DQ: Synthetic Data-Quality Detection Benchmark

## Status

Novel benchmark designed for MedCLI. There is no upstream paper or external benchmark release; the goal of this note is to capture the design rationale before integration so the source assets, verifier semantics, and label-generation logic are all owned by this repo.

## Task

Given a corrupted copy of an EHR dataset, the agent must identify which rows have been deliberately mutated. The dataset is a 100-patient subset of MIMIC-IV-demo v2.2, but the agent is not told the data source (the obfuscation is described below). Four tasks ship: one per error family plus a fourth combined task that mixes all three families. For each per-family task a single error family is applied across every table where it is meaningful, exercising all sub-variants of that family.

## Data source

The benchmark builds on the public MIMIC-IV-demo v2.2 (`https://physionet.org/files/mimic-iv-demo/2.2/`). Only eight tables are used: `patients`, `admissions`, `labevents`, `prescriptions`, `d_labitems`, `icustays`, `chartevents`, `d_items`. Total compressed footprint is ~8 MB. The demo is publicly accessible without PhysioNet credentials, so the benchmark can be downloaded and rebuilt from raw assets at Docker image build time.

## Error families

Three top-level families, each implemented by a deterministic injector keyed on a per-task random seed (see `INJECTOR_REGISTRY` in `scripts/ehr_data_quality/inject.py`):

- **`impossible_value`** — single-row implausibility. Five sub-types:
  - `range_extreme`: `valuenum` replaced with a value sampled from a per-itemid implausible band (HR/BP/temp/SpO₂ in chartevents; creatinine/glucose/potassium/sodium in labevents). Sampled, not constant, so the agent can't grep for a sentinel like `999.9`.
  - `decimal_shift`: lab `valuenum` × 10 (kept inside the per-itemid plausible range so this sub-type is not subsumed by `range_extreme`).
  - `decimal_shift_rx`: prescription `dose_val_rx` × 10 or 100.
  - `unit_confusion`: lab `valuenum` rewritten with a wrong-unit conversion factor (e.g., creatinine mg/dL × 88.42 with `valueuom` left unchanged).
  - `valueuom_mismatch`: `valueuom` swapped to a wrong unit string while `valuenum` is unchanged. Detectable by joining against `d_labitems`.

- **`inconsistency`** — disagreeing duplicates. Two sub-types, both two-row clusters where flagging *either* row catches the cluster:
  - `in_table_conflict`: an additional row appended in the same table with the same `subject_id`/`itemid` but `valuenum × 1.10–1.50` (varied per row), `charttime` jittered ±5 min, fresh `labevent_id`/`pharmacy_id` drawn from gaps in the natural range, and `value` synced to the new `valuenum`.
  - `cross_table_conflict`: a synthetic `chartevents` row injected against a `labevents` anchor for the same patient/charttime/measurement (via `LAB_CHART_PAIRS`); the chart `valuenum` differs by ×1.30–1.70 (rounded to per-itemid `DEVICE_PRECISION`); the row carries the patient's actual `icustays.stay_id` so it passes an FK check.

- **`demographic_conflict`** — patient demographics contradict cross-table evidence. Four sub-types, with **clusters expanded to include every row that legitimately reveals the contradiction** (the mutated row plus all sex-marker drugs, sex-specific lab events, and ref-range labs for that patient — flagging any one catches the cluster):
  - `gender_via_patients_flip`: `patients.gender` flipped for a patient who has at least one sex-marker drug or sex-specific lab as evidence.
  - `gender_via_prescription_swap`: a neutral `prescriptions.drug` overwritten with an opposite-sex marker drug (e.g., Tamsulosin onto a female patient).
  - `gender_via_ref_range_swap`: a sex-specific lab's `ref_range_lower`/`ref_range_upper` overwritten with the *opposite-sex* canonical band per `SEX_REF_RANGES` (e.g., a male hemoglobin row claims [12.0, 15.5] — the F-typical band).
  - `age_via_patients_change`: a geriatric-drug carrier's `anchor_age` overwritten with `5.0`.

The Weiskopf-and-Weng EHR-data-quality dimensions (completeness, plausibility, conformance, currency, concordance) are covered in aggregate by these three families without trying to be a 1:1 mapping.

A prototype `temporal_violation` family (within-row contradictions like `dischtime < admittime`, `starttime > stoptime`) was implemented and removed: the pristine demo contains real-world temporal anomalies (charttime/storetime ordering, home-meds preceding admission) that an agent with sound EHR reasoning would correctly flag, but those are absent from our injected-only label set, so they hurt precision unfairly. An orphan-FK family was prototyped but removed for being trivially detectable via a single anti-join.

## Labels and metric

Every injection emits one or more rows in a hidden `labels.csv` (CSV for human-readable diff review) keyed on `(table, row_id, error_family, error_subtype, field, original_value, corrupted_value, severity, cluster_id)`. `_row_id` is a sha1-derived synthetic primary key added to every table at corruption time so downstream identification is uniform across tables that lack a natural single-column PK. `cluster_id` groups rows that are interchangeable for recall credit — flagging *any* row in a cluster catches it.

The agent submits a CSV at `/workspace/submission/flagged_rows.csv` with columns `(table, _row_id)` (extra columns are ignored). The verifier writes the per-trial scalars to `verifier/reward.json` (flat `dict[str, float|int]` per Harbor's pydantic schema) and the full diagnostic payload to `verifier/metrics.json`. The scored metric is **F1**:

- `recall` (cluster-level): `caught_clusters / total_clusters`.
- `precision` (row-level): of the agent's flagged rows, the fraction that appear in *some* labeled cluster.
- `f1` (harmonic mean): the canonical reward.
- `per_family_recall_*`, `per_subtype_recall_*`: promoted as flat `fam_*` / `sub_*` keys for cross-trial pooling by the uv-script aggregator.
- `turn_count`: informational, encoded as `-1` when missing (Harbor's reward-json schema disallows None).

`reward.txt` is deliberately *not* written: Harbor reads it first when present, which would mask the rich `reward.json` payload that the launcher and aggregator depend on.

F1 (recall + precision) is intentional. Cluster-level recall handles the legitimate "any row in the cluster suffices" semantics for demographic_conflict and inconsistency. Row-level precision penalizes flag-everything strategies. The injectors close several synthetic-tell shortcuts (sentinel sampling, value↔valuenum sync, float-artifact rounding, natural-range fresh PKs, real `stay_id` FK lookup, opposite-sex canonical band swap) so detection requires legitimate EHR reasoning rather than artifact-grepping.

## Anti-cheat

The benchmark relies on **source-name obfuscation** to deter the trivial "wget the pristine source and diff" attack:

- No agent-visible artifact mentions MIMIC, MIMIC-IV-demo, PhysioNet, the source URL, or the demo nature. The DuckDB file is named `ehr.duckdb`. The instruction calls the data "an EHR dataset" generically. The agent is also explicitly instructed not to use the internet to look up reference values or attempt to re-download the source dataset.

A container-level egress block (e.g., `/etc/hosts` redirecting PhysioNet hostnames to `127.0.0.1`) was prototyped but is **not** active: `/etc/hosts` is read-only during `docker build`, so the redirect can't be installed at image-build time. A follow-up could add a runtime entrypoint script that writes to `/etc/hosts` at container startup if a stronger defense is needed.

Schema fingerprinting (well-known MIMIC table/column names and itemids) is not obscured. We accept that as a known limitation: schema-level obfuscation would break legitimate EHR prior knowledge an agent could bring.

In addition to source-name obfuscation, the injectors are designed to defeat synthetic-tell shortcuts that early agent runs revealed: range-extreme replacements are sampled (not constant), the `value` string is kept in sync with mutated `valuenum`, in-table conflict duplicates carry natural-range fresh PKs and ±5min charttime jitter, cross-table conflict synthetic chart rows look up real ICU stay IDs, multipliers are randomized, and `gender_via_ref_range_swap` overwrites with the canonical opposite-sex band rather than a relative shift. See `scripts/ehr_data_quality/README.md` for the full list.

## Why this is medically meaningful

EHR data quality is a documented source of clinical-decision-support failures, cohort-construction bias, and downstream-model error. Existing data-quality literature is largely descriptive (Weiskopf & Weng 2013 and follow-ups) or fielded as static QC pipelines; there is no widely-used benchmark for evaluating *agentic* detection of EHR data-quality issues end-to-end. This benchmark is the first MedCLI-internal artifact in that space and is intended to surface concrete differences in agent behavior on a long-horizon, tool-use-heavy task that maps directly to a real EHR-engineering responsibility.

## What MedCLI ships beyond the upstream resource

There is no upstream resource. What this benchmark contributes is:

- A fully reproducible corruption recipe with checked-in hidden labels (CSV, human-readable diff).
- A Harbor-native task layout with build-time data staging from PhysioNet, no credentials required, plus build-time `_verify_against` to catch injector drift before any agent run.
- F1 scoring (cluster-level recall × row-level precision) with per-family / per-subtype breakdown plus turn-count tracking, all flattened into a Harbor-compatible flat reward.json so the multi-task launcher can pool per-trial scalars.
- A reference solver and `manual_replay.sh` debug helper that establishes the heuristic-floor F1 (~0.03–0.12 per family).
- Multi-model baselines via `run_harbor_baselines_multitask.py` against both the `codex` and `copilot-cli` harnesses; results aggregated into a single `## ehr_data_quality` section in `paper/baselines.md`.

## Out of scope

- Credentialed full MIMIC-IV (would require PhysioNet auth and is unnecessary for a 100-patient benchmark).
- Schema-level obfuscation (would break legitimate EHR prior knowledge).
- Network-level (iptables / runtime `/etc/hosts`) egress filtering — current defense is source-name obfuscation only; a runtime entrypoint that rewrites `/etc/hosts` at container startup is a possible follow-up.
- Detection of *real* (un-injected) data-quality issues already present in the demo. The removed `temporal_violation` family is a concrete example: the demo has natural temporal anomalies that an agent will flag but our labels.csv doesn't credit.
