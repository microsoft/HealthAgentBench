# Exploring Scaling Laws for EHR Foundation Models (arXiv:2505.22964)

- Paper: https://arxiv.org/abs/2505.22964
- Title: *Exploring Scaling Laws for EHR Foundation Models*
- Authors: Sheng Zhang, Qin Liu, Naoto Usuyama, Cliff Wong, Tristan Naumann, Hoifung Poon
- Source read date: March 3, 2026

## Summary
This paper presents the first systematic examination of scaling principles for foundation models trained on electronic health records. By training transformer models on patient timeline data from MIMIC-IV across different sizes and computational budgets, the authors discover consistent scaling patterns — parabolic IsoFLOPs curves and power-law relationships between compute, model parameters, data size, and clinical utility.

The key finding is that EHR models demonstrate scaling behavior comparable to large language models, suggesting that the empirical scaling laws observed in NLP extend to the clinical domain. This provides practical guidance for resource-efficient development of EHR foundation models and has implications for predicting how larger models or more data will translate into improved clinical prediction.

The models are evaluated on downstream clinical prediction tasks including survival, length of stay, and readmission risk prediction from longitudinal patient data.

## Main Contributions
1. First systematic study of scaling laws for EHR foundation models, demonstrating power-law relationships between compute, parameters, data, and clinical utility.
2. Shows that EHR models exhibit scaling behavior comparable to LLMs, validating the foundation model paradigm for clinical data.
3. Provides practical guidance for compute-optimal training of EHR models.
4. Evaluated on downstream clinical prediction tasks (survival, length of stay, readmission) using MIMIC-IV.

## Method and Setup (High Level)
- Transformer models trained on patient timeline data from MIMIC-IV.
- Varied model sizes and computational budgets to map scaling curves.
- Measured parabolic IsoFLOPs curves and power-law scaling relationships.
- Downstream evaluation on clinical prediction tasks: survival, length of stay, readmission risk.

## Key Findings
- EHR foundation models follow scaling laws consistent with those observed in NLP.
- Larger models and more data yield predictable improvements in clinical prediction.
- Compute-optimal training configurations can be estimated from scaling curves.

## Limitations Noted by Authors
- Limited to MIMIC-IV (single-center ICU data).
- Scaling laws derived from relatively small model/data regimes compared to NLP.
- Downstream evaluation limited to standard clinical prediction benchmarks.

## Relevance to EHR Co-Scientist

### Alignment
- Directly relevant to clinical outcome prediction with longitudinal EHR input.
- Foundation model approach could power the predictive components of an agentic system.
- Scaling law findings inform decisions about model size and training data requirements.

### Differences
- Not agentic — purely a foundation model training study.
- Does not include evidence retrieval, explanation, or tool use.

### Implications for This Repository
1. Scaling laws provide guidance for choosing or training EHR embedding models as tools for the agent.
2. The downstream prediction tasks (survival, readmission, length of stay) align with the clinical outcome prediction task.
3. MIMIC-IV patient timelines used here could serve as a common data representation across multiple tasks.
