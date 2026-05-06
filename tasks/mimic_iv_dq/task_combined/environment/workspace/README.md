# Workspace orientation

This workspace contains a corrupted EHR dataset under `data/`. See
`../instruction.md` for the task description.

Layout:

- `data/csv/<table>.csv.gz`: eight EHR tables (gzipped CSVs).
- `submission/flagged_rows.csv`: write your answer here.

The schema across tables follows a typical hospital + ICU layout: patients,
admissions, lab events, prescriptions, ICU stays, chart events, plus two
dictionary tables (`d_labitems`, `d_items`).
