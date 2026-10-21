# mskchord_panc_surv_prob

## Overview

Build the strongest survival model you can for patients with pancreatic cancer. For every held-out patient, predict a survival-probability curve
from the available clinical, demographic, laboratory, and genomic features.

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

The `prediction` value must be a Python-style list of
`(time_years, survival_probability)` pairs. For example:

```text
[(0.0, 1.0), (0.5, 0.93), (1.0, 0.84), (1.5, 0.76)]
```

For every curve:

- Each point must contain exactly two numbers.
- Start at `(0.0, 1.0)`, end at 10.0 years, and include no later times.
- Times must be finite, nonnegative, and strictly increasing.
- Probabilities must be finite, between 0 and 1, and non-increasing.
- Probabilities should represent survival through the corresponding time.

CSV quoting is required because each prediction contains commas. A standard
CSV writer such as `pandas.DataFrame.to_csv(..., index=False)` handles this.

## Scoring

The verifier logs all survival-probability metrics:

- Coverage: fraction of expected patients with a unique, parseable curve.
- C-index: concordance based on the area under each predicted survival curve;
  higher is better.
- Censoring-adjusted MAE in years: error of predicted median survival after
  pseudo-observation adjustment for censoring; lower is better.
- Integrated Brier score at 0.5-year increments from 0.5 through 10 years,
  using linear curve interpolation; lower is better.

For cMAE, the predicted median is the first 0.5 crossing by linear
interpolation, or 10 years if the curve never falls below 0.5. Deaths use their
observed times. A censoring time `c` uses the jackknife KM-mean surrogate
`(n + 1) * mean(KM with c) - n * mean(training KM)`, clipped at the smaller of
30 years and maximum training follow-up.

The final reward is binary. Reward is 1.0 only when:

- Coverage is exactly 100%.
- C-index is strictly higher than both the Cox and RSF baselines.
- Censoring-adjusted MAE is strictly lower than both baselines.
- Integrated Brier score is strictly lower than both baselines.

Any missing, duplicate, unexpected, or malformed prediction prevents a
successful result.

## Constraints

- You have up to one hour.
- Internet access is unavailable. Use only the files in `/workspace/data` and
  the analysis packages preinstalled in the environment.
- Do not attempt to access held-out outcomes. They are not mounted during the
  agent run.
