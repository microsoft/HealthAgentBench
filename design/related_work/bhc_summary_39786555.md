# BHC Summary — Discharge Me! (PMID:39786555)

- Paper: https://pubmed.ncbi.nlm.nih.gov/39786555/
- Title: *A dataset and benchmark for hospital course summarization with adapted large language models*
- Journal: Journal of the American Medical Informatics Association, March 2025
- Source read date: March 3, 2026

## Summary
This work addresses the automatic generation of the Brief Hospital Course (BHC) section of hospital discharge summaries using clinical notes from MIMIC-IV. The BHC is a critical narrative section that describes a patient's entire hospital stay — from admission through diagnosis, treatment, and clinical trajectory to discharge. Writing BHCs is extremely time-consuming for clinicians, making it a high-value target for automated summarization.

The task is formulated as a long-document summarization problem where the input consists of multiple clinical notes from a single admission (nursing notes, physician notes, radiology reports, etc.) and the target output is the BHC section of the corresponding discharge summary. This is challenging due to extreme input lengths (often tens of thousands of tokens), the need to synthesize information across multiple note types, and the requirement for clinical accuracy.

Evaluation combines automatic metrics (ROUGE, BERTScore) with assessments of factual consistency. The shared task context also evaluated a separate Discharge Instructions section, but BHC is the more clinically demanding target.

## Main Contributions
1. Formalized BHC generation as a clinical summarization benchmark using real-world EHR data from MIMIC-IV.
2. Demonstrated feasibility of using LLMs for generating clinically meaningful hospital course summaries from multi-document clinical note inputs.
3. Provided baseline results and evaluation protocols combining standard NLG metrics with clinical relevance assessments.
4. Released task data and evaluation scripts through shared task infrastructure.

## Method and Setup (High Level)
- Input: all clinical notes (nursing, physician, radiology, pharmacy, etc.) from a single hospital admission, structured chronologically.
- Output: the Brief Hospital Course section of the discharge summary.
- Models: fine-tuned encoder-decoder models (BART, Longformer-Encoder-Decoder), instruction-tuned LLMs (GPT-4, LLaMA variants), retrieval-augmented approaches for extreme input lengths.
- Evaluation: ROUGE-1/2/L, BERTScore, and clinical accuracy metrics.

## Key Findings
- LLMs show strong performance but faithfulness/hallucination remains a significant concern.
- Extreme input length (10K-50K tokens) requires either efficient long-context architectures or intelligent note selection strategies.
- Automatic metrics (ROUGE, BERTScore) have known limitations in capturing clinical accuracy.

## Limitations Noted by Authors
- Hallucination risk: generated summaries may contain clinically inaccurate statements not grounded in source notes.
- Single-institution data (BIDMC via MIMIC-IV).
- Standard NLG metrics do not reliably capture clinical correctness.
- De-identification artifacts may affect training and evaluation.
- Flat note concatenation may not adequately capture temporal relationships.

## Relevance to EHR Co-Scientist

### Alignment
- Directly tests patient trajectory summarization — a core candidate task.
- Multi-document reasoning across heterogeneous note types mirrors the agentic challenge.
- Faithfulness requirements align with the need for evidence-grounded generation.

### Differences
- Pure summarization task; EHR Co-Scientist would use summarization as a tool for downstream tasks.
- Focused on free-text notes; does not integrate structured EHR data.

### Implications for This Repository
1. BHC generation could serve as both a standalone benchmark and a tool capability for downstream tasks.
2. The mismatch between automated metrics and clinical quality (as noted in tasks.md) suggests human evaluation or LLM-as-judge approaches are needed.
3. Hallucination detection should be a key evaluation dimension for any summarization component.
