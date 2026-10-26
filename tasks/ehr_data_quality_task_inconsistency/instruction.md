# EHR Data-Quality Detection

You are working inside a task environment that contains a copy of an EHR
dataset under `/workspace/data/`. Do a data quality check of the EHR
dataset and flag data entry errors belonging to certain error categories.
Submit the rows you identify at
`/workspace/submission/flagged_rows.csv`.

**You have up to 1 hour to complete this task.**

## Categories of errors to look for
You should flag all errors belonging to the following category:

1. **Conflicting records** — two records that should describe the same observation for the same patient at the same time but disagree.

Be thorough and make sure to flag all such errors.

## Submission format

A CSV with these columns:

- `table`: one of patients, admissions, labevents, prescriptions,
  d_labitems, icustays, chartevents, d_items
- `_row_id`: the value of the `_row_id` column for the row you are flagging

## Evaluation

The pass criteria are recall == 1.0 over the errors and precision >= 0.1
over the rows you flag, so the audit has to be targeted as well as
complete. Specifically:

- **Error-cluster recall:** recall must equal `1.0`. For an error that spans
  multiple dataset rows, flagging at least one affected row counts as finding
  that error.
- **Row-level precision:** at least `0.1` of the rows written to
  `flagged_rows.csv` must be genuinely erroneous rows.

You may flag all affected rows for a multi-row error, but this is not required
for recall; flag only rows you have evidence are erroneous to preserve
row-level precision.

## Data

EHR tables are at `/workspace/data/csv/<table>.csv.gz` (gzipped CSVs).

## Resources

You have 1 hour to complete the task. There is no internet access beyond the model
API. The container is configured for 2 CPUs, 4 GiB of memory, 10 GiB of disk, and no
GPU. System tools may report host resources, not these limits.
