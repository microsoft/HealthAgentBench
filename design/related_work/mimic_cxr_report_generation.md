# MIMIC-CXR Report Generation (v2.1.0)

- Upstream data: [MIMIC-CXR v2.1.0](https://physionet.org/content/mimic-cxr/2.1.0/) (free-text reports) and [MIMIC-CXR-JPG v2.1.0](https://physionet.org/content/mimic-cxr-jpg/2.1.0/) (512-px JPG frames + `mimic-cxr-2.0.0-split.csv.gz`).
- Access: credentialed PhysioNet user with signed DUA.
- Source read date: April 16, 2026.
- Upstream citations:
  - Johnson et al., *MIMIC-CXR, a de-identified publicly available database of chest radiographs with free-text reports* (Scientific Data, 2019). [doi:10.1038/s41597-019-0322-0](https://doi.org/10.1038/s41597-019-0322-0)
  - Johnson et al., *MIMIC-CXR-JPG, a large publicly available database of labeled chest radiographs* (arXiv:1901.07042, 2019).
  - Smit et al., *CheXbert: Combining Automatic Labelers and Expert Annotations for Accurate Radiology Report Labeling Using BERT* (EMNLP 2020). [arXiv:2004.09167](https://arxiv.org/abs/2004.09167)
  - Johnson et al., *MIMIC-CXR Database* report-generation prior work survey: Chen et al. (R2Gen, 2020), Miura et al. (Warm-Start, 2021), Endo et al. (CXR-RePaiR, 2021), Jeong et al. (RaDialog, 2024).

## Summary

The MIMIC-CXR dataset pairs each chest X-ray study with a free-text radiology report. The report generation task is to produce a clinically faithful report from the study's images (optionally conditioned on prior studies and structured metadata). This is one of the most-studied medical image-to-text tasks — it is benchmarked in nearly every recent radiology-report-generation paper and by multimodal clinical-AI evaluation suites (e.g., MIMIC-CXR leaderboards on the PhysioNet page, ReXGradient, CXRMate).

For MedCLI we integrate a **patient-aware, per-study** variant: each agent task corresponds to one target study from one patient, and the agent is given the patient's complete prior imaging history (images + reports + timestamps) as context.

## Why It Is Relevant to MedCLI

This benchmark fills the `Report generation` row in `design/tasks.md` and adds a genuinely multimodal task — the first in the repo that requires the agent to both read and visually interpret medical images. Success requires the agent to:

- navigate a longitudinal patient record laid out as timestamped folders
- read prior radiology reports for context
- call a multimodal tool (e.g. Codex's `view_image`) to actually see the target X-ray
- integrate visual observations with clinical history from priors
- draft FINDINGS and IMPRESSION in proper radiology prose
- format the output predictably enough for a pooled metric to score

Compared to purely text-based clinical benchmarks (EHRSQL, MedAgentBench, MEDS-ETL), this is the first task in the suite that is **visual and generative** simultaneously, and it stresses multi-turn tool use plus structured-output discipline.

## Important Design Implications

This is an **adapted benchmark**, not a mechanical import. Key design choices:

1. **Per-patient packaging.** Upstream leaderboards typically evaluate one (image → report) pair at a time. We instead give the agent the full patient history so the benchmark measures *longitudinal* reasoning (stable vs. new findings, interval-change language) in addition to isolated image-to-text. Each Harbor trial is one patient, not one image.
2. **FINDINGS + IMPRESSION only.** Ground-truth reports contain many sections (EXAMINATION, INDICATION, TECHNIQUE, COMPARISON, HISTORY, FINDINGS, IMPRESSION, and occasionally RECOMMENDATION / NOTIFICATION). The agent is given everything except FINDINGS and IMPRESSION and must generate only those two sections. This decouples the benchmark from boilerplate prediction and focuses scoring on the clinically load-bearing prose.
3. **Hidden target report.** The target study's full report never enters the container's filesystem. Prior studies' `report.txt` files are bind-mounted, but the target folder contains only JPGs. Ground truth is stored verifier-side in `tests/task_answer_key.json`.
4. **Eligibility filter.** Patients are only eligible if (a) they have 2+ studies with images and reports present, (b) their target (latest) study is in the MIMIC-CXR-JPG `test` split, and (c) the target report parses to non-empty FINDINGS and IMPRESSION sections. These constraints yield ~141 eligible patients from the ~2500 test-split patients.
5. **On-disk assets.** PhysioNet's per-study JPGs are large (~1 MB each, ~4.7 TB total dataset). We bootstrap only the per-task subset (both at generation time and opportunistically at container boot, under a shared flock).
6. **Pooled CheXbert F1 metric.** Per-trial BLEU/ROUGE-L are noisy on paraphrased radiology prose. We additionally compute pooled CheXbert F1-14 (micro/macro) via a `uv-script` aggregator that stacks per-trial CheXbert label vectors and calls `sklearn.classification_report`. This matches what most recent report-generation papers report (`f1chexbert==0.0.x` on PyPI) and is bit-identical to running `f1chexbert` directly on pooled text (proved by `scripts/mimic_report_gen/test_aggregation.py`).
7. **In-container labeling.** CheXbert labels are computed inside the verifier container (baked-in `f1chexbert` + pinned `transformers<5`, `scikit-learn<1.8`, `torch==2.4.1`, with the CheXbert BERT checkpoint pre-downloaded at build time). The aggregator then only pools flat scalar label fields from each trial's `reward.json`.

## Upstream Runtime Notes

At read-date April 16, 2026:

- `mimic-cxr-reports.zip` on PhysioNet v2.1.0 contains one `.txt` per study, organized as `files/pXX/p<subject>/s<study>.txt`. 293,234 reports.
- `mimic-cxr-jpg` v2.1.0 uses the same tree layout under `files/pXX/p<subject>/s<study>/<dicom>.jpg`. 377,110 DICOM rows in metadata.
- Credentialed access is required. Downloads use HTTP basic auth with `PN_USER` / `PN_PASS`.
- Dataset-level split file (`mimic-cxr-2.0.0-split.csv.gz`) is shared between CXR and CXR-JPG releases and assigns each `(dicom_id, subject_id, study_id)` to `train | validate | test`.
- `f1chexbert` (PyPI) uses `huggingface_hub.hf_hub_download(force_filename=...)`; on recent `huggingface_hub` the `force_filename` argument is a no-op, so a small path-normalizer is required to land the `chexbert.pth` file where `f1chexbert` expects. Our `scripts/mimic_report_gen/chexbert_labeler.py` handles this.

## Implications for This Repository

1. This benchmark becomes the first multimodal, generative task in the MedCLI suite.
2. Task-level artifacts live under `tasks/mimic_report_gen/<patient>_<target_study>/`; assets under `scripts/mimic_report_gen/assets/` (gitignored); job config at `jobs/mimic_report_gen.yaml`.
3. The metric pipeline relies on a new Harbor feature (`metrics: uv-script`) and proves out a clean pattern for complex pooled metrics that cannot be computed from per-trial scalars alone: compute per-sample ingredients in the verifier, emit them as numeric fields in `reward.json`, and pool in a uv-script aggregator. This pattern is reusable for future benchmarks (e.g. clinical-NLI or cohort-overlap metrics).
4. The benchmark integration adds a concrete example of a benchmark with a non-trivial build layer (torch + BERT inside the task container). Cached rebuilds are free; cold builds are ~5 min one-time.
