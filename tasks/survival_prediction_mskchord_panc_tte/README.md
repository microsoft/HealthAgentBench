# `survival_prediction_mskchord_panc_tte`

This task evaluates time-to-death predictions for the MSK-CHORD pancreatic cancer cohort using the Survprompt split and TTE_OS metrics.

**Success criteria:** reward 1.0 requires 100% parseable predictions and strict
improvement over both the Cox and random survival forest baselines on C-index,
censoring-adjusted MAE, and integrated Brier score.

## Data setup

MSK-CHORD is not distributed with HealthAgentBench.
Download the dataset from [here](https://github.com/clinical-data-mining/msk-chord-figures-public/tree/main/data) and place the PANC cohort file at:

```text
assets/survival_prediction/mskchord/panc_dx_1st_seq_OS.csv
```

The raw file is mounted only into the bootstrap container. The agent receives
labeled training examples and unlabeled test examples through a Docker volume;
the held-out outcomes remain verifier-only.

## Run this task

```bash
uv run harbor run \
  --path tasks/survival_prediction_mskchord_panc_tte \
  --agent claude-code \
  --model claude-opus-4-8 \
  --agent-kwarg reasoning_effort=xhigh \
  --agent-kwarg disallowed_tools="WebSearch WebFetch" \
  --n-attempts 3 --n-concurrent 1
```

## Benchmark alignment

The task uses fold 0 from Survprompt's five-fold split with seed 20. There is
one HealthAgentBench task per prediction format and cohort rather than one task
per fold. Predictions use the Survprompt `TTE_OS` representation, and verifier thresholds come from
the Cox and RSF runs produced with that same cohort, split, and representation.

## Data & references

- Survprompt: <https://github.com/microsoft/survprompt>
