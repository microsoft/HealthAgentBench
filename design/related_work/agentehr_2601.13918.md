# AgentEHR (arXiv:2601.13918)

- Paper: https://arxiv.org/abs/2601.13918
- Title: *AgentEHR: Advancing Autonomous Clinical Decision-Making via Retrospective Summarization*
- Source read date: March 3, 2026

## Summary
AgentEHR proposes an agentic framework that leverages LLMs to perform clinical outcome prediction by interacting with EHR data in a multi-step, tool-augmented manner. Rather than encoding EHR data into fixed representations for a classifier, the framework equips an LLM-based agent with tools to query, retrieve, and reason over structured EHR data — diagnoses, procedures, medications, lab results, and clinical notes. The agent iteratively retrieves relevant patient information, synthesizes evidence, and produces predictions for tasks such as in-hospital mortality, readmission, and length-of-stay.

A key contribution is the **RetroSum** (retrospective summarization) framework that dynamically re-evaluates interaction history to prevent information loss during multi-step reasoning. This achieves up to 29.16% improvement over baselines and 92.3% reduction in interaction errors.

The framework is evaluated on MIMIC-based clinical prediction benchmarks, comparing against traditional deep learning baselines (GRU, Transformer-based) and direct LLM prompting strategies.

## Main Contributions
1. Agentic EHR interaction framework where an LLM agent actively queries and retrieves information through tool use, rather than passively receiving a fixed patient representation.
2. RetroSum — a retrospective summarization mechanism that re-evaluates interaction history to prevent information loss during long reasoning chains.
3. Evidence-grounded clinical predictions accompanied by retrieved evidence and explicit reasoning chains.
4. Comprehensive evaluation on standard MIMIC clinical prediction tasks against both ML/DL and LLM baselines.

## Method and Setup (High Level)
- Agent architecture: an LLM serves as the central reasoning engine with a task description and tool suite.
- Tool suite: tools to query structured EHR tables — diagnoses, medications, lab values, procedures, demographics.
- ReAct-style loop: think → call tool → observe → decide whether to gather more data or predict.
- RetroSum: periodically re-summarizes the interaction history to preserve key information.
- Prediction output includes both the prediction (high/low risk) and evidence trail.
- Evaluated via AUROC, AUPRC, F1 on MIMIC benchmarks.

## Key Findings
- Agentic approach matches or outperforms direct prompting, especially for patients with long, complex records.
- Selective, iterative retrieval helps the agent focus on clinically relevant information rather than being overwhelmed.
- RetroSum substantially reduces information loss and interaction errors.
- Performance gains most pronounced for tasks requiring cross-modality synthesis (lab trends + medication changes).
- Produces interpretable reasoning traces that clinicians can audit.

## Limitations Noted by Authors
- High computational cost: multiple LLM calls per patient.
- Performance tied to underlying LLM's medical knowledge.
- Primarily handles structured/semi-structured EHR data.
- Evaluated on MIMIC only (single-center ICU).
- Offline evaluation; real-world deployment considerations not addressed.

## Relevance to EHR Co-Scientist

### Alignment
- Directly implements the agentic paradigm for clinical outcome prediction — the same architecture this project targets.
- Evidence-grounded predictions with reasoning traces align with the project's emphasis on interpretability.
- Tool-use approach mirrors how EHR Co-Scientist agents would interact with databases.

### Differences
- Focuses on prediction tasks; EHR Co-Scientist covers a broader task spectrum (ETL, cohort construction, report generation).
- Does not address unstructured clinical notes or imaging integration.

### Implications for This Repository
1. AgentEHR is the most directly comparable prior work for the clinical outcome prediction task.
2. The RetroSum mechanism is relevant for any multi-step agentic task that risks information loss.
3. Evaluation protocol (AUROC, AUPRC + evidence quality) can be adopted.
4. The computational cost findings should inform system design decisions.
