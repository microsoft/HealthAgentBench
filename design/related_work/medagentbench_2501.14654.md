# MedAgentBench (arXiv:2501.14654)

- Paper: https://arxiv.org/abs/2501.14654
- Repository: https://github.com/stanfordmlgroup/MedAgentBench
- DeepWiki: https://deepwiki.com/stanfordmlgroup/MedAgentBench
- Title: *MedAgentBench: A Realistic Virtual EHR Environment to Benchmark Medical LLM Agents*
- Source read date: March 3, 2026

## Summary
MedAgentBench introduces a benchmark for evaluating LLMs as **medical agents** in an interactive EHR-like setting, rather than as static question-answering systems. The benchmark includes:

- 300 clinician-authored tasks across 10 categories
- 100 realistic, de-identified patient profiles
- ~785k total clinical records represented via FHIR resources
- A FHIR-compliant environment (HAPI FHIR-based) for tool/API interaction

The paper evaluates multiple frontier and open models in a constrained agent loop (up to 8 interaction rounds, pass@1 metric). Best reported overall success rate is **69.67%** (Claude 3.5 Sonnet v2), indicating meaningful progress but substantial room for improvement in reliability.

## Main Contributions
1. A clinically grounded, agent-oriented benchmark beyond medical QA exams.
2. A realistic interactive FHIR environment that can support API-based agent evaluation.
3. Baseline results across 12 LLMs with breakdowns by query vs action tasks and difficulty.

## Method and Setup (High Level)
- Task categories include retrieval, aggregation, documentation-style updates, ordering, referral, and medication actions.
- Agent can choose between GET request, POST request, or finish action each round.
- Evaluation emphasizes strict single-attempt performance (pass@1), reflecting healthcare safety constraints.
- Action tasks require correct payload structure and decision logic, not just natural-language answers.

## Key Findings
- Current models are notably better on retrieval/query tasks than action/modification tasks.
- Frequent failures are formatting and protocol-following errors (invalid tool syntax, wrong answer format), not only medical reasoning gaps.
- Harder multi-step tasks remain unsaturated, suggesting benchmark headroom for future systems.

## Limitations Noted by Authors
- Simulated environment does not capture full real-world hospital coordination complexity.
- Cohort derived from a single institutional data source (potential representativeness limits).
- Initial benchmark scope (300 tasks, 100 patients) trades breadth for practical evaluation cost.

## Relevance to EHR Co-Scientist
This paper is highly relevant to this project’s objective of tool-augmented EHR agents.

### Alignment
- Both focus on **agentic workflows** over clinical data rather than static QA.
- Both rely on explicit tool invocation and multi-step reasoning.
- Both emphasize realistic, verifiable task completion.

### Differences
- MedAgentBench is centered on **FHIR API interaction** in a simulated EHR server.
- EHR Co-Scientist is broader, including SQL-centric analysis over MIMIC-style data, ETL, cohorting, temporal reasoning, and report generation.

### Implications for This Repository
1. MedAgentBench can serve as an external benchmark target through `scripts/medagentbench/` orchestration and task manifests under `tasks/<task_type>/sources/medagentbench/`.
2. A FHIR adapter/tool integration can extend current evaluation beyond SQL-first settings.
3. Error analysis should explicitly track:
   - tool-call syntax validity,
   - output schema adherence,
   - action reliability under multi-step constraints.
4. Query-vs-action split is useful as a core dashboard metric for model and orchestrator iteration.

## Suggested Citation Note
If this repo’s paper/discussion references benchmark context for medical agents, cite MedAgentBench as evidence that state-of-the-art models remain far from deployment-grade reliability on action-oriented clinical tasks.
