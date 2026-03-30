# MedCalc-Bench (arXiv:2406.12036)

- Paper: https://arxiv.org/abs/2406.12036
- Repository: https://github.com/ncbi-nlp/MedCalc-Bench
- Title: *MedCalc-Bench: Evaluating Large Language Models for Medical Calculations*
- Source read date: March 23, 2026

## Summary

MedCalc-Bench is a benchmark for evaluating large language models on medical calculations rather than descriptive medical QA. It contains more than 1,000 manually reviewed instances across 55 medical calculation tasks. Each instance includes a patient note, a question asking for a specific medical calculation, a ground-truth answer, and a step-by-step explanation.

The benchmark targets quantitative clinical reasoning built from equations and rule-based decision support logic, reflecting how clinicians use calculators in real settings.

## Main Contributions

1. A medical benchmark centered on calculation-heavy reasoning rather than factual question answering.
2. Coverage of 55 medical calculators spanning equation-driven and rule-based tasks.
3. Instance design that includes both final answers and step-by-step derivations for error analysis.

## Method and Setup (High Level)

- Data sources include public patient-note corpora and synthesized notes.
- Task coverage includes equation-style and rule-based calculators across categories such as lab, physiology, dates, dosing, risk, severity, and diagnosis.
- Each example pairs a patient note with a concrete calculation request and validated answer.
- The paper evaluates multiple open and closed models under direct, chain-of-thought, and one-shot chain-of-thought prompting.

## Key Findings

- Existing LLMs are substantially better at some medical calculations with prompting support, but remain unreliable for clinical deployment.
- Common failures include extracting the wrong entities, choosing the wrong equation or rule, and performing arithmetic incorrectly.
- Medical calculation remains a distinct capability gap relative to standard medical QA benchmarks.

## Limitations Noted by Authors

- The benchmark is not an interactive or tool-using environment.
- Performance is measured on static note-and-question examples rather than longitudinal workflows.
- Some data is synthesized during curation, which may limit realism relative to fully native clinical workflows.

## Relevance to MedCLI

MedCalc-Bench is relevant as a benchmark for quantitative medical reasoning over clinical text-like inputs.

### Alignment

- Focuses on clinically grounded reasoning rather than generic arithmetic.
- Provides a benchmark with explicit error modes that are useful for agent evaluation.
- Fits the broader MedCLI goal of testing health-task competence beyond descriptive QA.

### Differences

- It is a static benchmark, not an interactive terminal or environment benchmark.
- It centers on medical calculators and note understanding rather than live data access or multi-step workflow execution.
- Integration would likely look more like packaged case evaluation than Harbor environment simulation.

### Implications for This Repository

1. MedCalc-Bench is a plausible planned benchmark if MedCLI expands into benchmark modes beyond interactive environments.
2. If integrated, it should likely be represented as a calculator-reasoning benchmark with a distinct task interface.
3. The benchmark is especially useful if the repo wants a strong quantitative-reasoning complement to EHR/workflow benchmarks.
