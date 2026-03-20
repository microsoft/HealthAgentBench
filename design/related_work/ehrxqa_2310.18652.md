# EHRXQA (arXiv:2310.18652)

- Paper: https://arxiv.org/abs/2310.18652
- Repository: https://github.com/baeseongsu/ehrxqa
- Title: *EHRXQA: A Multi-Modal Question Answering Dataset for Electronic Health Records with Chest X-ray Images*
- Source read date: March 3, 2026

## Summary
EHRXQA is a large-scale benchmark for multi-modal question answering over EHRs that integrates both structured/tabular clinical data and chest X-ray images. The benchmark evaluates whether AI systems can answer clinically meaningful questions requiring joint reasoning over heterogeneous EHR data modalities — a capability critical for real-world clinical decision support but underexplored in existing QA benchmarks.

The dataset is built on MIMIC-IV (structured EHR tables) and MIMIC-CXR (chest X-ray images and radiology reports). Questions are programmatically generated using templates grounded in clinical logic, ensuring broad coverage and reproducibility. Questions are categorized by modality requirement (table-only, image-only, or multi-modal) and by reasoning type (temporal, counting, comparison, logical operations).

Evaluation uses exact-match accuracy. The benchmark includes a program-based question generation pipeline that produces both natural language questions and corresponding executable programs, enabling transparent and verifiable answer derivation.

## Main Contributions
1. First large-scale multi-modal QA benchmark for EHRs jointly covering structured clinical tables and chest X-ray images.
2. Systematic question generation pipeline using compositional, template-based programs ensuring diverse question types and verifiable ground-truth answers.
3. Fine-grained evaluation taxonomy by modality (table, image, table+image) and reasoning skill.
4. Baseline experiments with text-to-SQL, VQA models, and multi-modal LLMs revealing substantial room for improvement on cross-modal reasoning.

## Method and Setup (High Level)
- Data foundation: MIMIC-IV for structured EHR tables, MIMIC-CXR for chest X-ray images.
- Composable functional programs (CLEVR-style) verbalized into natural language questions via templates.
- Questions tagged as table-only, image-only, or multi-modal (table + image).
- Baselines: text-to-SQL for table questions, medical VQA for image questions, multi-modal LLMs and pipeline approaches for cross-modal questions.

## Key Findings
- Table-only questions handled reasonably well by strong text-to-SQL systems, though complex temporal and multi-hop reasoning remains challenging.
- Image-only questions feasible for specialized medical VQA models but accuracy drops for nuanced or rare findings.
- Multi-modal questions are the most challenging, with all baselines showing significant performance degradation.
- Compositional and temporal reasoning consistently difficult across all modality types.

## Limitations Noted by Authors
- Constructed from MIMIC (single-center ICU data), limiting generalizability.
- Template-generated questions may not fully capture diversity and ambiguity of real clinical questions.
- Image modality restricted to chest X-rays; other imaging modalities not covered.
- Focuses on factoid-style QA with exact-match evaluation; does not capture open-ended clinical reasoning.

## Relevance to EHR Co-Scientist

### Alignment
- Extends factual QA to the multi-modal setting (structured data + imaging), which is the realistic clinical scenario.
- Compositional multi-step reasoning mirrors how an agentic system decomposes complex queries into sub-tasks.
- Naturally supports evaluation of tool-using agents (SQL engines, image classifiers).

### Differences
- Template-based closed-form QA does not capture open-ended reasoning, multi-turn dialogue, or action tasks.
- EHR Co-Scientist may need to go beyond chest X-rays to other modalities.

### Implications for This Repository
1. EHRXQA can benchmark multi-modal QA capabilities, especially for agents that combine SQL tools with vision models.
2. The cross-modal performance gap highlights a key research direction for agentic systems.
3. The executable program representation could inform how agents decompose and verify their reasoning steps.
