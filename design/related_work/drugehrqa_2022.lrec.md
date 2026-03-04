# DrugEHRQA (LREC 2022)

- Paper: https://aclanthology.org/2022.lrec-1.117.pdf
- Title: *DrugEHRQA: A Question Answering Dataset on Structured and Unstructured Electronic Health Records For Medicine Related Queries*
- Source read date: March 3, 2026

## Summary
DrugEHRQA is a question answering dataset focused on medication-related queries over electronic health records. It combines both structured (tabular) and unstructured (clinical notes) EHR data from MIMIC-III to answer drug-related clinical questions. The dataset targets a specific and clinically important niche — questions about medications, prescriptions, drug interactions, and pharmacological information within patient records.

The benchmark is designed to test whether QA systems can handle the complexity of medication-related queries that span structured prescription records and free-text clinical notes. This dual-source setup reflects the reality of clinical practice where medication information is scattered across multiple data formats.

## Main Contributions
1. A dedicated medication-focused QA dataset built on MIMIC-III combining structured and unstructured data sources.
2. Addresses a clinically important niche — drug-related queries that are among the most common information needs in clinical settings.
3. Demonstrates the challenge of integrating structured prescription data with unstructured clinical narratives for question answering.

## Method and Setup (High Level)
- Built on MIMIC-III clinical database.
- Questions focus on medication-related information: prescriptions, drug administration, indications, and related clinical context.
- Requires reasoning over both structured tables (prescriptions, pharmacy records) and unstructured text (discharge summaries, clinical notes).

## Key Findings
- Drug-related QA over EHRs remains challenging due to the need to reconcile information across structured and unstructured sources.
- Models struggle with queries requiring temporal reasoning about medication timelines.

## Limitations Noted by Authors
- Limited to MIMIC-III (single-center ICU data).
- Drug-specific focus may not generalize to broader clinical QA scenarios.
- Published in 2022; may not reflect capabilities of current LLMs.

## Relevance to EHR Co-Scientist

### Alignment
- Directly relevant to medication reconciliation and drug-related factual QA tasks.
- Multi-source (structured + unstructured) requirement aligns with agentic workflows that must query multiple data types.

### Differences
- Focused on QA rather than agentic actions (ordering, prescribing).
- Older benchmark; may need to be combined with more recent evaluations.

### Implications for This Repository
1. Can supplement EHRSQL for medication-specific QA evaluation.
2. The structured+unstructured integration challenge is a good test for agentic systems that use multiple tools.
