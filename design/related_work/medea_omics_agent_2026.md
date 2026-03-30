# Medea (bioRxiv 2026)

- Paper: https://www.biorxiv.org/content/10.64898/2026.01.16.696667v1
- Title: *Medea: An omics AI agent for therapeutic discovery*
- Venue: bioRxiv
- Posted: January 20, 2026
- Source read date: March 23, 2026

## Summary

Medea is an AI agent for long-horizon omics analyses aimed at therapeutic discovery. It takes an omics objective and executes a transparent multi-step analysis using tools, with explicit verification at intermediate steps and a consensus stage that reconciles evidence across datasets, tools, and literature.

The system uses 20 tools spanning single-cell and bulk transcriptomics, cancer vulnerability maps, pathway knowledge bases, and machine-learning models. The paper evaluates Medea across 5,679 analyses in target identification, synthetic lethality reasoning, and immunotherapy response prediction.

## Main Contributions

1. A verification-aware biomedical AI agent for long-horizon omics analysis.
2. A modular architecture spanning planning, code execution, literature reasoning, and evidence reconciliation.
3. Broad evaluation across thousands of analyses and multiple biomedical discovery settings.

## Method and Setup (High Level)

- Medea has four main modules:
  - research planning with context and integrity verification
  - code execution with pre-run and post-run checks
  - literature reasoning with evidence-strength assessment
  - consensus over datasets, tools, and literature
- Tooling spans transcriptomic datasets, vulnerability maps, pathway knowledge, and predictive models.
- Evaluations vary LLM backbones, tool sets, objectives, and agent modules.

## Key Findings

- The paper reports performance gains over existing approaches in target identification, synthetic lethality, and immunotherapy response prediction.
- The authors emphasize that the gains come from transparent, verification-aware analyses rather than workflow speed alone.
- The system maintains low failure rates and calibrated abstention in the reported experiments.

## Limitations and Integration Questions

- This is an agent/system paper, not a benchmark release with a clean standalone task package.
- The domain is omics and therapeutic discovery rather than current MedCLI benchmark domains such as EHR workflows or clinical calculators.
- Integrating anything inspired by this work would likely require substantial new asset, tool, and environment design.

## Relevance to MedCLI

This paper is relevant as a strong example of verification-aware biomedical agents.

### Alignment

- Emphasizes long-horizon tool use, explicit intermediate verification, and evidence reconciliation.
- Treats transparent reasoning as a first-class requirement.
- Expands the space of health-agent tasks beyond EHR and calculator settings.

### Differences

- Focused on omics and therapeutic discovery rather than clinical operations or patient-level EHR tasks.
- Presented as a system study, not a directly reusable benchmark.
- Likely needs a substantially different runtime/tooling model from current repo benchmarks.

### Implications for This Repository

1. Medea is a strong review candidate if MedCLI wants to expand into omics or discovery-oriented agent tasks.
2. It should remain in review until there is a deliberate scope decision on whether therapeutic-discovery workflows belong in this repo.
3. If pursued later, it would likely motivate a new benchmark family centered on data-analysis agents with code execution and scientific evidence synthesis.
