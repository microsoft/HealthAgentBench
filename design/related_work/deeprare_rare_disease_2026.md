# DeepRare / Rare Disease Diagnosis Agent (Nature 2026)

- Paper: https://www.nature.com/articles/s41586-025-10097-9
- Title: *An agentic system for rare disease diagnosis with traceable reasoning*
- Journal: Nature
- Published: February 18, 2026
- Source read date: March 23, 2026

## Summary

This paper presents DeepRare, an agentic large-language-model system for rare disease differential diagnosis. The system processes heterogeneous clinical inputs, including free-text descriptions, structured Human Phenotype Ontology (HPO) terms, and genetic testing results, then produces ranked diagnostic hypotheses with transparent reasoning linked to verifiable medical evidence.

DeepRare is evaluated across nine datasets spanning 2,919 diseases and 14 medical specialties. The paper positions the system as a diagnostic decision-support agent rather than a static classifier.

## Main Contributions

1. An agentic architecture for rare disease differential diagnosis with explicit evidence-linked reasoning.
2. Integration of more than 40 specialized tools and up-to-date knowledge sources across phenotype, genotype, and retrieval workflows.
3. Large-scale evaluation across public and in-house datasets, plus expert review of reasoning trace validity.

## Method and Setup (High Level)

- Inputs can include free-text clinical descriptions, structured HPO terms, raw VCF files, or combinations of these.
- The system uses an MCP-inspired three-tier architecture:
  - a central LLM host with memory
  - specialized agent servers with tools
  - outer-layer medical knowledge sources
- The workflow includes iterative evidence gathering, hypothesis generation, self-reflection, and ranked diagnosis output.
- Outputs include top-K candidate diseases plus transparent reasoning chains tied to medical evidence.

## Key Findings

- DeepRare outperforms comparison methods substantially on rare-disease diagnosis benchmarks.
- In HPO-based evaluations, the paper reports strong Recall@1 and Recall@3 gains over the next-best method.
- In multi-modal tests with phenotype and genomic inputs, the system improves over established rare-disease diagnostic tools such as Exomiser.
- Expert review reported high agreement with the system’s reasoning chains, supporting the traceability claim.

## Limitations and Integration Questions

- This is a diagnosis-support agent/system paper, not a benchmark paper in the same sense as MedAgentBench or EHRSHOT.
- The evaluation spans multiple datasets and internal sources, which may complicate clean external reproduction.
- The task shape depends on phenotype/genotype tooling and rare-disease resources that are outside the current repo scope.

## Relevance to MedCLI

This paper is highly relevant to MedCLI’s broader interest in agentic health workflows.

### Alignment

- Strong emphasis on tool-using medical agents rather than static QA.
- Explicit reasoning traces and evidence grounding match MedCLI’s interest in inspectable agent behavior.
- Multi-modal clinical inputs broaden the view of what health-agent tasks could look like.

### Differences

- The paper presents a diagnostic system, not a drop-in benchmark artifact.
- The domain is rare disease diagnosis with phenotype and genomic inputs, not general EHR or calculator workflows.
- Reproducing this in repo form would require a different asset and environment model.

### Implications for This Repository

1. This is a strong review candidate for future benchmark or task-family inspiration.
2. It should stay in review until there is a clearer decision on whether MedCLI wants rare-disease diagnosis and genotype-aware tasks in scope.
3. If pursued later, it would likely motivate a new benchmark family rather than a small extension of current MedAgentBench-style packaging.
