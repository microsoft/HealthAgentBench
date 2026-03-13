# EHRSQL (arXiv:2301.07695)

- Paper: https://arxiv.org/abs/2301.07695
- Repository: https://github.com/glee4810/EHRSQL
- Title: *EHRSQL: A Practical Text-to-SQL Benchmark for Electronic Health Records*
- Source read date: March 3, 2026

## Summary
EHRSQL is a practical text-to-SQL benchmark designed specifically for electronic health record databases. It addresses the gap between general-domain text-to-SQL benchmarks (Spider, WikiSQL) and the real-world needs of healthcare professionals querying EHR data using natural language. The benchmark collects questions from actual hospital staff — physicians, nurses, and other healthcare workers — to ensure questions reflect genuine clinical information needs.

The benchmark is built on two widely used EHR databases: MIMIC-III and eICU. A key distinguishing feature is the inclusion of **unanswerable questions** — natural language questions that cannot be answered by the underlying database schema. This forces models to not only generate correct SQL but also recognize when a question falls outside the scope of what the database can answer, a critical safety requirement for clinical deployments.

The evaluation framework measures execution accuracy and the model's ability to abstain from answering unanswerable questions. This reliability-focused evaluation reflects the practical requirement that clinical text-to-SQL systems must avoid generating plausible but incorrect queries.

## Main Contributions
1. Clinically grounded benchmark with questions collected from real hospital personnel rather than crowd workers, ensuring authentic clinical information needs.
2. Introduced unanswerable question detection as a critical safety requirement for clinical text-to-SQL systems.
3. Dual-database evaluation on MIMIC-III and eICU, enabling cross-database generalization assessment.
4. Reliability-aware evaluation metrics that balance SQL generation accuracy with the ability to correctly reject unanswerable queries.

## Method and Setup (High Level)
- Healthcare professionals pose questions they would naturally ask an EHR database, spanning patient demographics, lab results, vital signs, medications, diagnoses, procedures, and administrative data.
- Each answerable question is paired with a gold-standard SQL query.
- Baseline experiments include sequence-to-sequence models (T5-based), in-context learning with LLMs (Codex/GPT-3), and established text-to-SQL architectures.
- Evaluated in both standard (generate SQL for all) and reliability (answer or abstain) settings.
- Time-sensitive questions requiring knowledge of "current" date/time are included.

## Key Findings
- State-of-the-art text-to-SQL models that perform well on general-domain benchmarks show significantly degraded performance on EHRSQL, indicating EHR-specific challenges (medical terminology, temporal reasoning, large schemas).
- LLMs with in-context learning showed competitive performance, particularly with relevant schema information and examples.
- Unanswerable question detection proved challenging: systems tended to either over-generate SQL or over-abstain.
- Temporal reasoning (e.g., "in the last 24 hours," "during the current admission") was identified as a particularly challenging category.

## Limitations Noted by Authors
- Limited to two ICU-focused EHR databases (MIMIC-III and eICU), which may not represent outpatient or general ward EHR systems.
- English only.
- SQL queries target specific database schemas; generalization to proprietary EHR systems (Epic, Cerner) requires additional adaptation.
- Focuses on single-turn question answering; does not address multi-turn conversational interactions.

## Relevance to EHR Co-Scientist

### Alignment
- Directly tests the core capability needed for factual question answering over structured EHR data.
- The unanswerable question detection maps to safety requirements of agentic systems — an agent must know when it cannot reliably answer.
- Temporal reasoning tests are essential for real-time clinical decision support.

### Differences
- EHRSQL focuses on single-turn text-to-SQL; EHR Co-Scientist targets multi-step agentic workflows.
- Does not cover unstructured clinical notes or imaging data.

### Implications for This Repository
1. EHRSQL can serve as a foundational benchmark for the factual QA task under `benchmarks/`.
2. The unanswerable question detection capability should be a core evaluation dimension for any agentic EHR QA system.
3. Temporal reasoning performance should be tracked as a distinct metric.
