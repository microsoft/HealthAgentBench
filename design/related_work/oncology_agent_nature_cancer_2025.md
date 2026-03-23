# Autonomous Oncology Decision-Making Agent (Nature Cancer 2025)

- Paper: https://www.nature.com/articles/s43018-025-00991-6
- Title: *Development and validation of an autonomous artificial intelligence agent for clinical decision-making in oncology*
- Journal: Nature Cancer
- Published: June 6, 2025
- Source read date: March 23, 2026

## Summary

This paper presents an autonomous clinical AI agent for multimodal decision-making in oncology. The system uses GPT-4 as the central reasoning model and augments it with precision-oncology tools, retrieval, and web search to support personalized treatment planning over realistic cancer cases.

The agent integrates histopathology, radiology, structured clinical information, and oncology knowledge resources. It was evaluated on 20 realistic multimodal gastrointestinal oncology cases and compared with GPT-4 alone.

## Main Contributions

1. A multimodal oncology decision-support agent that autonomously selects and applies specialized tools.
2. Integration of pathology, radiology, genomics-related inference, calculators, retrieval, and web search into one clinical agent workflow.
3. Evaluation on realistic patient cases with expert assessment of tool use, clinical conclusions, and citation quality.

## Method and Setup (High Level)

- Core LLM: GPT-4.
- Tools include:
  - histopathology vision transformers for MSI, KRAS, and BRAF prediction
  - MedSAM for radiology segmentation
  - radiology-report generation tooling
  - calculator
  - Google, PubMed, and OncoKB search/retrieval
  - curated oncology document repository
- Each case is handled in two stages:
  - autonomous tool selection and application
  - evidence-grounded response generation with citations

## Key Findings

- The integrated agent markedly outperforms GPT-4 alone on the study’s oncology decision benchmark.
- The paper reports strong tool-selection accuracy and strong rates of correct clinical conclusions.
- Tool use and retrieval substantially improve response completeness over vanilla LLM prompting.

## Limitations and Integration Questions

- This is a system-validation paper, not a released benchmark in the same style as MedAgentBench.
- Evaluation uses 20 realistic cases, which is valuable but still small.
- Reproducing the setup would require specialized oncology tools and multimodal data access beyond the current repo scope.

## Relevance to MedCLI

This paper is highly relevant to MedCLI’s broader agenda around tool-using clinical agents.

### Alignment

- Strong emphasis on autonomous tool selection, multimodal reasoning, and evidence-grounded outputs.
- Evaluates realistic clinical decision-making instead of static medical QA.
- Shows a concrete path for integrating specialist medical tools around a central LLM agent.

### Differences

- Focused specifically on oncology and multimodal precision-medicine workflows.
- Presented as a system study rather than a reusable benchmark artifact.
- Would require a materially different environment and tool stack from the repo’s current benchmark integrations.

### Implications for This Repository

1. This is a strong review candidate for future benchmark or task-family design.
2. It should remain in `Review Queue` until there is a deliberate scope decision on oncology-specific multimodal agents.
3. If pursued later, it would likely motivate a separate benchmark family for multimodal clinical decision support rather than a small extension of existing benchmark layouts.
