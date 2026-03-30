# EHRSHOT (arXiv:2307.02028)

- Paper: https://arxiv.org/abs/2307.02028
- Repository: https://github.com/som-shahlab/ehrshot-benchmark
- Title: *EHRSHOT: An EHR Benchmark for Few-Shot Evaluation of Foundation Models*
- Source read date: March 23, 2026

## Summary

EHRSHOT is a structured EHR benchmark for evaluating clinical foundation models in low-label and few-shot settings. It releases a longitudinal cohort of 6,739 de-identified Stanford patients, canonical train/validation/test splits, and labels for 15 prediction tasks. The benchmark is built around structured coded data rather than clinical text, images, or an interactive tool-using environment.

The associated paper also releases CLMBR-T-base, a 141M-parameter transformer pretrained on 2.57M patient timelines, and uses EHRSHOT to measure few-shot adaptation across multiple task families.

## Main Contributions

1. A longitudinal structured-EHR benchmark that is broader than ICU-only datasets and explicitly designed for few-shot evaluation.
2. A set of 15 prediction tasks covering operational outcomes, lab anticipation, diagnosis assignment, and chest X-ray finding prediction.
3. Public release of a pretrained structured-EHR foundation model and a reproducible evaluation pipeline.

## Method and Setup (High Level)

- Data source: Stanford Medicine STARR, transformed into a lightweight OMOP-style CSV serialization.
- Cohort: 6,739 adult patients with 41.6M coded observations and 921,499 visits.
- Task families:
  - operational outcomes
  - anticipating lab test values
  - assignment of new diagnoses
  - anticipating chest X-ray findings
- Evaluation style: few-shot classification over canonical splits and k-shot samples, not interactive agent execution.

## Key Findings

- Longitudinal structured EHR data supports a broader and more realistic benchmark than ICU-only datasets such as MIMIC-style setups.
- Pretrained foundation models show meaningful gains in few-shot settings, but there is still significant headroom across many tasks.
- Benchmark release plus model-weight release materially improves reproducibility for clinical foundation-model research.

## Limitations Noted by Authors

- Only structured data is released; no clinical text or images.
- Cohort size is relatively small compared with the full source health-system population.
- Tasks are predictive classification tasks rather than open-ended or workflow-based clinical tasks.
- Generalization outside Stanford Medicine remains unclear.

## Relevance to MedCLI

EHRSHOT is relevant as a non-agentic but high-value benchmark for structured EHR modeling.

### Alignment

- Uses longitudinal structured EHR data rather than narrow ICU snapshots.
- Covers multiple clinically meaningful task families over coded patient timelines.
- Provides a concrete external benchmark for health ML systems operating over structured records.

### Differences

- EHRSHOT is a few-shot prediction benchmark, not an interactive terminal or tool-using agent benchmark.
- Its primary interface is dataset files and task labels, not action-taking over a live environment.
- Integration would likely require a different task environment shape than MedAgentBench.

### Implications for This Repository

1. EHRSHOT is a plausible benchmark candidate if MedCLI expands beyond interactive agent tasks into longitudinal structured-EHR prediction tasks.
2. Any integration should be framed as a different benchmark mode from interactive tool-use benchmarks like MedAgentBench.
3. If added, task generation and evaluation would likely emphasize reproducible dataset/task packaging rather than live environment simulation.
