# mskchord_prostate_tte

## Overview

Build the strongest survival model you can for patients with prostate cancer. For every held-out patient, predict the time to death or overall survival in
days from the available clinical, demographic, laboratory, and genomic
features.

You may use any modeling approach. Iterate freely; only the final submission
written to `/workspace/submission/predictions.csv` is scored.

## Inputs

The following files are available under `/workspace/data/`:

- `train.csv`: labeled training patients. It contains `sample_id`, feature
  columns, `observed_time_days`, and `event_observed`.
- `test_examples.csv`: held-out patients with `sample_id` and the same feature
  columns, but no outcomes.
- `manifest.json`: split metadata and the feature-column list.

`event_observed` is true when death was observed and false when the survival
time is right-censored. Missing feature values may be present.
The prediction landmark is first sequencing, and `observed_time_days` is
follow-up after that landmark (`stop - entry`). Treat all supplied features,
including `progressed` and `MAX_*` fields, as the fixed landmark snapshot.

## Output

Write `/workspace/submission/predictions.csv` with exactly these columns:

```csv
sample_id,prediction
```

Each held-out patient `sample_id` must appear exactly once and must match a row
in `test_examples.csv`.

Treat `sample_id` only as an opaque submission key. Do not use its value,
numeric components, ordering, or any transformation of it as input to
prediction, feature engineering, stratification, calibration, or model
selection.

The `prediction` value must be one finite, nonnegative survival time in days.
For example:

```csv
sample_id,prediction
P-0000012,730
```

Integer and decimal values are accepted. Do not include units or explanatory
text in the prediction cell.

## Scoring

The verifier logs the Survprompt TTE_OS metrics:

- Coverage: fraction of expected patients with a unique, parseable time.
- Harrell's C-index: use negative predicted survival time in days as risk;
  higher is better.
- Confidence-weighted MAE-PO (pseudo-observation MAE; Qi et al., 2023),
  measured in years; lower is better.
- Graf IPCW integrated Brier score: estimate censoring from training
  outcomes. Convert each scalar prediction to survival 1 through the
  predicted time and 0 afterward; lower is better. The ten-year limit
  applies to the Brier grid, not the submitted survival time.

For MAE-PO, convert days to years using 365.25 days per year and use the
training outcomes as the Kaplan-Meier (KM) reference. Deaths use their
observed times with weight 1. A censored patient at time `c` uses the
jackknife target `(n + 1) * mean(KM with c) - n * mean(training KM)`,
upper-capped at the smaller of 30 years and maximum training follow-up,
with weight `1 - S_train(c)`. Report the weighted mean absolute error.

The benchmark's KM mean uses trapezoidal integration over training death
times plus the last follow-up, starting at `(0, 1)`. Positive terminal
survival is extended linearly to zero at `t_last / (1 - S_last)`. The
augmented mean retains that grid; append `c` only when it is at or beyond
the last knot. Confidence weights use right-continuous KM over all training
follow-up times; beyond the last time, continue the first-to-last observed
KM-knot slope, flooring survival at zero.

For Brier scoring, use right-continuous reverse KM, with deaths removed
before censoring at tied times. The candidate grid is 0.5, 1.0, ..., 10.0
years; the verifier retains times at or above minimum test follow-up and
strictly below both maximum test and maximum training follow-up. Integrate
by the trapezoidal rule divided by the retained time span; use the single
score if only one time remains. An unavailable metric cannot pass.

The final reward is binary. Reward is 1.0 only when:

- Coverage is exactly 100%.
- C-index is strictly higher than both the Cox and RSF baselines.
- Censoring-adjusted MAE is strictly lower than both baselines.
- Integrated Brier score is strictly lower than both baselines.

Any missing, duplicate, unexpected, or malformed prediction prevents a
successful result.

## Constraints

- You have up to one hour, 16 CPUs, 32 GiB RAM and 32 GiB storage; no GPU.
- Internet access is unavailable. Use only the files in `/workspace/data` and
  the analysis packages preinstalled in the environment.
- Do not attempt to access held-out outcomes. They are not mounted during the
  agent run.
