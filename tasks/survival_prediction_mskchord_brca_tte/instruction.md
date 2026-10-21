# mskchord_brca_tte

## Overview

Build the strongest survival model you can for patients with breast cancer. For every held-out patient, predict the time to death or overall survival in
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

The verifier reports coverage, Harrell's C-index, MAE-PO, and integrated
Brier score. Coverage requires one valid prediction per held-out patient.

- **Harrell's C-index:** use `sksurv.metrics.concordance_index_censored`
  (scikit-survival 0.28.0, default risk-tie tolerance `1e-8`) with risk equal
  to the negative submitted survival time in days. Higher is better.
- **Time estimate for MAE-PO:** divide the submitted time in days by 365.25.
  Lower error is better.
- **Probabilities for Brier scoring:** convert each scalar time to a
  deterministic curve with survival 1 at evaluation times less than or
  equal to the predicted time, and 0 afterward. Lower Brier score is better.
  Scalar predictions may exceed 10 years; only the Brier grid is limited
  to that candidate horizon.

### MAE-PO conventions

The censoring-adjusted error is **confidence-weighted MAE-PO (mean absolute error with
pseudo-observations)**, based on Qi et al., *An Effective Meaningful Way to
Evaluate Survival Models* (ICML 2023), Section 3.6, with the benchmark-specific conventions below.
Use years throughout this calculation; one year is 365.25 days. The reference
Kaplan-Meier (KM) estimator uses the supplied training outcomes, not the
held-out outcomes. At a KM knot, the risk set includes training patients
with follow-up at or beyond that time; deaths at a tied time occur while
patients censored at that time are still at risk.

- An observed death uses its observed follow-up as the target and weight 1.
  A patient censored at time `c` uses the appended-censor jackknife target
  `(n + 1) * augmented KM mean - n * training KM mean`, where `n` is the
  number of training patients. Its confidence weight is `1 - S_train(c)`.
  MAE-PO is the sum of weighted absolute errors divided by the sum of weights;
  if every weight is zero, use the unweighted mean absolute error.
- **KM-mean integration convention:** retain distinct training death times
  and the maximum training follow-up time, prepend `(0, 1)`, and integrate
  the resulting time/survival knots by the trapezoidal rule. This is not the
  rectangular area of the KM step function or a restricted-mean calculation.
  If the final knot `(t_last, S_last)` has positive survival, append a
  zero-survival knot at `t_last / (1 - S_last)` before integration.
- For the augmented mean, keep that training-time grid and training death
  counts; increase each risk-set count by one at grid times at or before
  `c`, then recompute the KM products. Do not insert `c` as another integration
  knot unless it is at or beyond the last retained time; in that case append
  `(c, last augmented survival)`, including when the times are equal. Apply the same integration/tail convention.
- Upper-cap censored targets at the smaller of 30 years and the maximum
  training follow-up. There is no lower clipping of these targets, and
  observed-death targets are not capped.
- For confidence weights, `S_train(c)` is the right-continuous KM step value
  from all distinct training follow-up times, with value 1 before the first
  time. Beyond the last time, extrapolate using the slope joining the first
  and last distinct observed training-time KM knots (excluding the
  artificial `(0, 1)` integration knot) and floor survival at zero; use slope
  zero if those observed times coincide. This weight calculation is separate from the trapezoidal
  KM-mean calculation above.

### Integrated Brier score conventions

Use the **Graf et al. (1999) inverse-probability-of-censoring-weighted Brier
score**, with censoring estimated from the training outcomes, as implemented
by `sksurv.metrics.brier_score` in scikit-survival 0.28.0. Retain that
implementation's conventions: estimate censoring by reverse KM (remove
deaths before counting censoring at tied times), and evaluate censoring
survival right-continuously at observed times and grid times, not at the
left limit of an observed death time. Zero censoring survival contributes
zero inverse weight; do not add an arbitrary positive floor. Patients
censored at a grid time contribute neither the death nor survival term at
that time, but remain in the averaging denominator. If this library call
raises, IBS is unavailable; this can occur when a validation follow-up
exceeds training support and terminal censoring survival is positive, even
after grid clipping. Do not silently drop those patients or extrapolate
censoring probabilities to force a finite score.

The candidate evaluation times are 0.5, 1.0, ..., 10.0 years. The verifier
keeps only times at or above the minimum held-out follow-up and strictly
below both the maximum held-out follow-up and maximum training follow-up.
Thus the effective horizon can be shorter than 10 years; it is not a fixed
10-year integration interval. During training-fold validation, apply this
same support rule using the validation outcomes for the held-out support and
the fitting outcomes for the training support. Test outcomes remain hidden;
the final support is selected by the verifier.

Integrate the finite retained Brier scores by the trapezoidal rule and divide
by the span between the first and last retained times, rather than averaging
grid-point scores. If only one finite score remains, use it directly; no
finite score means this metric is unavailable and cannot satisfy the reward.

Method references (identification only; internet access remains unavailable):
[Qi et al., 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC12396822/) and
[scikit-survival 0.28.0 metrics](https://scikit-survival.readthedocs.io/en/v0.28.0/api/metrics.html).

The final reward is binary. Reward is 1.0 only when:

- Coverage is exactly 100%.
- C-index is strictly higher than both the Cox and RSF baselines.
- Censoring-adjusted MAE is strictly lower than both baselines.
- Integrated Brier score is strictly lower than both baselines.

Any missing, duplicate, unexpected, or malformed prediction prevents a
successful result.

## Constraints

- You have up to one hour, 16 CPUs, 32 GiB RAM and 32 GiB storage; no GPU.
- Preinstalled analysis packages include numpy 2.5.1, pandas 2.3.3, scipy
  1.18.0, scikit-learn 1.9.0, scikit-survival 0.28.0 and lifelines 0.30.3.
- Internet access is unavailable. Use only the files in `/workspace/data` and
  the analysis packages preinstalled in the environment.
- Do not attempt to access held-out outcomes. They are not mounted during the
  agent run.
