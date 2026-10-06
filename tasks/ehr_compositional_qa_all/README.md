# `ehr_compositional_qa_all`

The full **EHR Compositional QA** benchmark as a single task: all 51 questions
(12 MIMIC-IV concepts, 51 question variants) that the five question-type tasks partition.
Use it for a whole-benchmark pass/fail; use the per-type tasks for diagnosis.

**Training:** `train.json` holds 1020 labeled examples, twenty per question variant.
Test patients never appear in `train.json` (patient-disjoint split); each test question
is asked about a stay for which every input the label depends on is recorded.

**Pass condition:** all **51/51** answers correct in a valid submission.
Integer-valued answers must be within 0.5 (strictly); continuous answers within
`max(1% of |gt_answer|, 0.001)`. Each question carries its `tolerance` in the answer key.
The verifier reports diagnostic accuracy separately from the binary reward.

Data: public MIMIC-IV-demo v2.2, downloaded by a bootstrap service at runtime; no dataset
credentials required. The database contains raw hospital/ICU tables only.

## Run

```bash
uv run harbor run --path tasks/ehr_compositional_qa_all \
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
