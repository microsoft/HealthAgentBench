# Medical Coding Reproducibility (arXiv:2304.10909)

- Paper: https://arxiv.org/abs/2304.10909
- Repository: https://github.com/JoakimEdin/medical-coding-reproducibility
- Title: *Automated Medical Coding on MIMIC-III and MIMIC-IV: A Critical Review and Replicability Study*
- Venue: ACM SIGIR 2023
- Source read date: March 3, 2026

## Summary
This work provides a critical review and large-scale replicability study of automated medical coding — the task of assigning ICD codes to clinical notes such as hospital discharge summaries. The authors identify significant methodological inconsistencies across prior published work that make fair comparison between methods difficult or impossible, including differences in data preprocessing, text truncation lengths, train/validation/test splits, and evaluation protocols.

The authors re-implement and evaluate several prominent automated medical coding models under a single unified experimental framework using MIMIC-III and MIMIC-IV. Their standardized pipeline covers data preprocessing, tokenization, label handling, and evaluation with consistent macro- and micro-averaged F1, precision, recall, and AUC-ROC metrics.

A key finding is that when evaluated under consistent conditions, the performance gap between simpler models and more complex state-of-the-art architectures narrows substantially. PLM-ICD (a pretrained language model-based approach) is among the strongest performers when fairly compared.

## Main Contributions
1. Systematic identification of reproducibility issues in the automated medical coding literature, cataloging inconsistencies in preprocessing, data splits, truncation, and evaluation.
2. A unified, open-source benchmarking framework re-implementing multiple prominent models under identical experimental conditions.
3. Fair re-evaluation showing performance differences between methods are often smaller than previously reported.
4. Standardized data processing pipelines for MIMIC-III and MIMIC-IV for community reuse.

## Method and Setup (High Level)
- Re-implements models including CAML, MultiResCNN, LAAT, PLM-ICD within a single PyTorch codebase.
- Consistent data loading, preprocessing, tokenization, text truncation, label space definitions (ICD-9 codes, full-code and top-50 settings).
- Standard Mullenbach et al. split for MIMIC-III; extended experiments on MIMIC-IV.
- Metrics: micro-F1, macro-F1, micro-AUC, macro-AUC.

## Key Findings
- Prior reported performance gains are inflated due to inconsistent experimental setups.
- Under fair comparison, PLM-ICD is a top performer but the margin over simpler baselines (CAML, MultiResCNN) is smaller than originally claimed.
- Text truncation length has a surprisingly large effect on performance.
- Choice of data split and label filtering significantly impacts results.

## Limitations Noted by Authors
- Limited to MIMIC-III and MIMIC-IV (single-center ICU data).
- Only English-language discharge summaries.
- Framed as multi-label classification from text; does not capture full complexity of real-world medical coding workflows.
- Focuses on ICD-9/ICD-10 codes; does not address CPT/HCPCS procedure codes.

## Relevance to EHR Co-Scientist

### Alignment
- Directly relevant to cross-schema ETL where ICD code assignment is a core transformation step.
- The reproducibility issues identified are analogous to challenges in cross-schema ETL — subtle pipeline differences cause large discrepancies.

### Differences
- Focuses on ICD code prediction rather than schema mapping or data transformation.
- Not agentic; purely a classification benchmark.

### Implications for This Repository
1. The standardized evaluation framework could serve as a validation harness for any agentic medical coding pipeline.
2. Demonstrates that simpler well-tuned models can be competitive — relevant for choosing tool components in an agentic system.
3. The finding that pipeline choices (truncation, splits) dominate model choice is a cautionary tale for ETL evaluation.
