# EHR Data-Quality Detection

You are working inside a task environment that contains a copy of an EHR
dataset under `/workspace/data/`. A subset of rows has been deliberately
mutated to introduce data-quality issues. Your job is to identify which
rows are problematic and submit them at
`/workspace/submission/flagged_rows.csv`.

Be selective: both missing real issues and flagging legitimate rows will
affect your score. Submit only rows you have strong evidence are
problematic.

## Categories of errors to look for

The injected issues fall into one category. Focus your detection on it — do not flag rows that are merely unusual but plausible.

1. **Impossible values** — a single field value that is implausible for the measurement type (e.g., physiologically impossible, or implausible for the displayed unit, or off by an obvious order of magnitude).

Stay within this category. Generic "looks weird" outliers, clinically extreme but plausible
values, or rare-but-legitimate variation are not what we are looking for.

## Submission format

A CSV with these columns:

- `table`: one of patients, admissions, labevents, prescriptions,
  d_labitems, icustays, chartevents, d_items
- `_row_id`: the value of the `_row_id` column for the row you are flagging

## What you have

- `/workspace/data/csv/<table>.csv.gz`: the EHR tables (gzipped CSVs)
- Standard tools available: pandas, duckdb, numpy, pyarrow, sqlite3 — load
  the CSVs into whichever you prefer for querying.

## Rules

Do **not** use the internet to look up reference ranges, canonical units,
or the source dataset. Do **not** attempt to re-download a "pristine" copy
of the data and diff it against `/workspace/data/`. Solve the task using
only the data in `/workspace/data/` and standard analytical tools
(pandas, duckdb, numpy). Internet is enabled only to allow your runtime
to function; using it to retrieve answers is considered cheating.
