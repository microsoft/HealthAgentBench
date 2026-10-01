# mskchord_crc_surv_prob_no_train

## Overview

Build the strongest survival model you can for patients with colorectal cancer. For every held-out patient, predict a survival-probability curve
from the available clinical, demographic, laboratory, and genomic features.

You may use any modeling approach. Iterate freely; only the final submission
written to `/workspace/submission/predictions.csv` is scored.


## Inputs

The following files are available under `/workspace/data/`:

- `test_examples.csv`: held-out patients with `sample_id` and feature columns,
  but no outcomes.
- `manifest.json`: split metadata and the feature-column list.

No labeled `train.csv` is provided. Missing feature values may be present.

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

- Times must be finite, nonnegative, and strictly increasing.
- Probabilities must be finite and between 0 and 1.
- Probabilities should represent survival through the corresponding time.
- Include enough of the curve to support evaluation from 0.5 through 10 years.

CSV quoting is required because each prediction contains commas. A standard
CSV writer such as `pandas.DataFrame.to_csv(..., index=False)` handles this.

## Scoring

The verifier logs all survival-probability metrics:

- Coverage: fraction of expected patients with a unique, parseable curve.
- C-index: concordance based on the area under each predicted survival curve;
  higher is better.
- Censoring-adjusted MAE in years: error of predicted median survival after
  pseudo-observation adjustment for censoring; lower is better.
- Integrated Brier score over the supported 0.5-to-10-year grid; lower is
  better.

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
- Do not attempt to access training outcomes or held-out outcomes. They are not mounted during the
  agent run.
