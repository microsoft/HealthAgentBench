# `ehr_compositional_qa_temporal`

One of five tasks in HealthAgentBench's **EHR Compositional QA** category, partitioned
by question type. This task holds the **14 `temporal` questions**: time-anchored values and event timings.
Concepts covered: apsiii, first_day_sofa, kdigo_stages, lods, meld, norepinephrine_equivalent_dose, oasis, sapsii, sepsis3, sirs, sofa.

**Training:** `train.json` holds 1020 labeled examples, twenty per question variant for all 60 variants in the benchmark (shared across the six compositional-QA tasks).
Test patients never appear in `train.json` (patient-disjoint split). Questions can involve
missing data: a score input that was never measured (scored by the reference convention) or
a quantity that does not exist for the patient (expected answer `"not_applicable"`). Every
missing-data pattern used in a test question appears in at least three training examples of
the same question variant.

**Pass condition:** all **14/14** answers correct in a valid submission.
Integer-valued answers must be within 0.5 (strictly); continuous answers within
`max(1% of |gt_answer|, 0.001)`; a `"not_applicable"` answer must match exactly. Each question
carries its `tolerance` in the answer key.
The verifier reports diagnostic accuracy separately from the binary reward.

Data: public MIMIC-IV-demo v2.2, downloaded by a bootstrap service at runtime; no dataset
credentials required. The database contains raw hospital/ICU tables only.

## Run

```bash
uv run harbor run --path tasks/ehr_compositional_qa_temporal \
  --agent codex --model gpt-6-astra --agent-kwarg reasoning_effort=xhigh \
  --n-attempts 1 --n-concurrent 1
```

Run the whole category with `uv run harbor run -p tasks --include-task-name 'ehr_compositional_qa_*' -a <agent> -m <model>`.

## Bootstrap and label isolation

Harbor starts a one-shot `bootstrap` service before `main`. Bootstrap downloads
the public demo on first use, builds a raw-only DuckDB, and stages it into a named
volume. A shared host cache under `assets/ehr_compositional_qa/` avoids repeated
downloads; only bootstrap can access that cache. Main mounts the raw-data volume
read-only and cannot access bootstrap files or any test labels.

Grading uses Harbor's `environment_mode = "separate"`: a dedicated verifier image
built from `tests/` contains the answer key. Harbor transfers the submission into
that container after the agent finishes. It never uploads `/tests` or the answer
key into main. The verifier has no internet access and no shared task-data volume.
Verifier metrics omit expected answer values so shared logs do not disclose gold
labels.
