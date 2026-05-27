# lab_anemia

## Overview

This is a **clinical event prediction task** on real electronic health
record (EHR) data. Each prediction row is defined by a **patient** and a
specific **prediction time point**. Your goal is to use the patient's
longitudinal clinical history — every observed event (diagnosis, drug,
lab, procedure, visit) **strictly before** the prediction time — to
predict the value of a target label at that time point. The same pattern
applies to every row: read the patient's past timeline up to a moment,
decide the label at that moment.

## Task

For each hemoglobin lab measurement, predict whether the result will
indicate anemia. Prediction is made immediately before the result is
recorded (i.e. on the basis of the patient's history up to that
moment, before the numeric value is available). Time horizon: the
next lab result.

## Label semantics

1 = the resulting hemoglobin value is < 12 g/dL (any of: mild [<12 g/dL],
    moderate [<11 g/dL], or severe [<7 g/dL] anemia).
0 = the resulting hemoglobin value is >= 12 g/dL (normal range).

You have access to a **train** split and a **val** split with labels, plus
a longitudinal event log for all patients in those splits. Explore the
data, learn a strategy from train and val, and apply it to a held-out
**test** split provided without labels. Submit a probability for each
test row.

**Push for the strongest predictions you can produce.** You are free to
use any approach. Iterate freely: only the final submission you write to
`predictions.csv` is scored.

## Inputs (under `/workspace/data/`)

- `train_labels.csv` — labels for the train split. Columns:
  `patient_id, prediction_time, label`.
- `val_labels.csv` — labels for the val split (same schema as train).
- `test_examples.csv` — `(patient_id, prediction_time)` rows you must
  predict on. **No labels.**
- `events.csv` — longitudinal flat event log for all patients in this
  task's train + val + test cohorts. Columns:
  `patient_id, start, end, code, value, unit, visit_id, omop_table`.
  Each row is one observed clinical event. The format is a single flat
  table (not the canonical OMOP CDM multi-table schema); `omop_table`
  records which OMOP source table the event came from
  (`condition_occurrence`, `drug_exposure`, `measurement`,
  `procedure_occurrence`, `visit_occurrence`, `visit_detail`,
  `observation`, `note`, `device_exposure`, `death`, `person`). The
  `code` field uses standard OMOP vocabularies with a prefix:
  e.g. `SNOMED/...`, `LOINC/...`, `RxNorm/...`, `CVX/...`, `ICD10PCS/...`,
  `CPT4/...`, plus demographic/visit metadata codes like `Gender/F`,
  `Race/...`, `Visit/IP`. `value` is populated for numeric events
  (e.g. lab results) and empty otherwise. The file is read-only and
  large (~1-2 GB after slicing); stream it with
  `pandas.read_csv(..., chunksize=...)` or `pyarrow` if memory is tight.

  **Anti-leakage rule:** when scoring or training a row at
  `prediction_time = T`, only use events with `start < T` for that
  patient. Events at or after `T` are not legitimately observable.

- `splits/person_id_map.csv` — patient → split mapping (so you can
  cross-check which patients are train/val/test).

## Output

Write `/workspace/submission/predictions.csv` with columns:


    patient_id,prediction_time,probability


Each row should correspond to a row in `test_examples.csv`. Each
probability column is a **continuous value anywhere in `[0, 1]`** (any
real number, not restricted to discrete bins) expressing **how confident
you are that the label is positive (1)**:

  - the closer to **1**, the more confident you are the label is positive,
  - the closer to **0**, the more confident you are the label is negative.

Submit raw continuous probabilities/scores, not hard 0/1 predictions and
not coarse buckets. For multilabel tasks, each label column is independent
(one continuous confidence per finding; they do not need to sum to 1
across columns).

The verifier matches rows by `(patient_id, prediction_time)` and rejects
submissions with missing rows.

## Scoring

Your submission will be scored with **AUROC** (Area Under the Receiver
Operating Characteristic curve) against the held-out test labels. For
multilabel tasks the score is the mean AUROC across the label columns.

## Constraints

- **Time budget: ~1 hour** for the full task.
- You have internet access and may install any Python packages or
  external tools you need.
