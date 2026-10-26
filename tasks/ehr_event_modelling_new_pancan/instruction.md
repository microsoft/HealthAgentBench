# new_pancan

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

Predict whether the patient will have their first diagnosis of pancreatic
cancer within the next year. Pancreatic cancer is defined as an
occurrence of the code SNOMED/372003004, as well as its children codes in
the ontology. Prediction is made at 11:59 PM on the day of discharge from
an inpatient visit. All discharges where the patient already has an
existing pancreatic-cancer diagnosis are ignored.

## Label semantics

1 = first-time pancreatic cancer diagnosis with onset 1 to 365 days after
    the prediction time.
0 = no such diagnosis in the (1, 365]-day window.

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
  (e.g. lab results) and empty otherwise.

  **Anti-leakage rule:** when scoring or training a row at
  `prediction_time = T`, only use events with `start < T` for that
  patient. Events at or after `T` are not legitimately observable.

- `splits/person_id_map.csv` — patient → split mapping. Columns:
  `omop_person_id, split` (`omop_person_id` is the same identifier as
  `patient_id` in the other files; `split` is `train`, `val` or `test`).

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
not coarse buckets. Every value must be a finite number; an empty or
`NaN` probability counts as a missing row.

The verifier matches rows by `(patient_id, prediction_time)` and
**rejects the whole submission if any test row is missing**. Extra rows
not in `test_examples.csv` are ignored.

## Scoring

Your submission will be scored with **AUROC** (Area Under the Receiver
Operating Characteristic curve) against the held-out test labels. The
task counts as solved when your AUROC reaches or exceeds a fixed
reference AUROC.

## Resources

You have 1 hour to complete the task. There is no internet access beyond the model
API. The container is configured for 16 CPUs, 64 GiB of memory, 64 GiB of disk, and
no GPU. System tools may report host resources, not these limits.
