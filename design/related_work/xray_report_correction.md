# Chest X-ray Report Correction (xray_report_correction)

- Upstream data: [MIMIC-CXR v2.1.0](https://physionet.org/content/mimic-cxr/2.1.0/) (free-text reports, split file, metadata) and [MIMIC-CXR-JPG v2.1.0](https://physionet.org/content/mimic-cxr-jpg/2.1.0/) (512-px JPG frames).
- Access: credentialed PhysioNet user with signed DUA. Downloads use HTTP basic auth (`PN_USER` / `PN_PASS`).
- Source read date: April 16, 2026.
- Upstream citations:
  - Johnson et al., *MIMIC-CXR, a de-identified publicly available database of chest radiographs with free-text reports* (Scientific Data, 2019). [doi:10.1038/s41597-019-0322-0](https://doi.org/10.1038/s41597-019-0322-0)
  - Johnson et al., *MIMIC-CXR-JPG, a large publicly available database of labeled chest radiographs* (arXiv:1901.07042, 2019).
  - Microsoft, *CheXprompt — clinical-error scoring of radiology reports with GPT-class LLMs* (github.com/microsoft/chexprompt, 2024).
  - Prior report-generation work: Chen et al. (R2Gen, 2020), Miura et al. (Warm-Start, 2021), Endo et al. (CXR-RePaiR, 2021), Jeong et al. (RaDialog, 2024).

## Summary

The MIMIC-CXR dataset pairs each chest X-ray study with a free-text radiology report. The report generation task is to produce a clinically faithful report from the study's images, optionally conditioned on prior studies and structured metadata. It is the canonical medical image-to-text task and is benchmarked in nearly every recent radiology-report-generation paper and multimodal clinical-AI evaluation suite.

For MedCLI we integrate a **patient-aware, per-study, manually-curated** variant: each agent task corresponds to one target study from one patient, the agent is given that patient's complete prior imaging history (images + reports + timestamps), and the gold target report is manually reviewed for clinical accuracy. Scoring is binary (pass/fail) via a **CheXprompt** majority vote on clinically-significant errors against the gold FINDINGS.

## Why It Is Relevant to MedCLI

This benchmark fills the `Report generation` row in `design/tasks.md` and adds a genuinely multimodal task — the first in the repo that requires the agent to both read and visually interpret medical images. Success requires the agent to:

- navigate a longitudinal patient record laid out as timestamped folders
- read prior radiology reports for context
- call a multimodal tool (e.g. Codex's `view_image`, Claude Code's image-aware Read) to actually see the target X-ray
- integrate visual observations with clinical history from priors
- draft FINDINGS and IMPRESSION in proper radiology prose
- format the output predictably so a single FINDINGS section can be extracted and scored

Compared to purely text-based clinical benchmarks (EHRSQL, MedAgentBench, MEDS-ETL), this is the first task in the suite that is **visual and generative** simultaneously, and it stresses multi-turn tool use plus structured-output discipline.

## Important Design Implications

This is an **adapted benchmark**, not a mechanical import. Key design choices:

1. **Per-patient packaging.** Upstream leaderboards typically evaluate one (image → report) pair at a time. We instead give the agent the patient's full history so the benchmark measures *longitudinal* reasoning (stable vs. new findings, interval-change language) in addition to isolated image-to-text. Each Harbor trial is one patient, not one image.
2. **FINDINGS + IMPRESSION only.** Ground-truth reports contain many sections (EXAMINATION, INDICATION, TECHNIQUE, COMPARISON, HISTORY, FINDINGS, IMPRESSION, occasionally RECOMMENDATION / NOTIFICATION). The agent is given everything except FINDINGS and IMPRESSION and must generate only those two sections. This decouples scoring from boilerplate prediction and focuses on the clinically load-bearing prose.
3. **Hidden gold, no test leakage.** The target study's full report never enters the agent's filesystem. Prior studies' `report.txt` files are bind-mounted; the target folder contains only JPGs. Gold FINDINGS is staged at `/tests/target_report.txt` by the bootstrap compose service and mounted into the verifier container only at verifier time. `tests/task_answer_key.json` and `target_report.txt` are gitignored.
4. **Opaque agent-visible identifiers.** Cases are named `case_01..case_10`; studies are `study_NN_<actual_timestamp>`; views are `view_NN.jpg`. MIMIC patient/study/dicom IDs never appear in any agent-visible surface, and the corpus name "MIMIC" is not mentioned in the instruction. This reduces the chance of memorized-answer leakage from training data.
5. **Manually curated 10-case suite.** Rather than sampling thousands of test-split patients and treating noisy upstream gold as truth, we hand-picked 10 cases that span common chest-X-ray phenotypes (clear lungs, cardiomegaly, ETT/IABP positioning, fluid overload, chest tubes, pneumothorax negation, etc.) and manually reviewed each gold FINDINGS for clinical accuracy. The hardcoded `(opaque_id, subject_id, target_study_id)` tuples in `scripts/xray_report_correction/generate_harbor_tasks.py` make the suite reproducible without checking in curation scripts.
6. **All MIMIC priors, not just radeval's one.** Where a curated case has priors, we enumerate *every* prior study for that patient from MIMIC's raw `metadata.csv.gz` (filtered to study datetimes strictly before the target). This gives the agent a true longitudinal trajectory rather than a single before-and-after pair.
7. **CheXprompt with 5-vote majority.** Per-trial BLEU/ROUGE-L are noisy on paraphrased radiology prose, and CheXbert F1 conflates negation with semantic accuracy. We use **CheXprompt** (a GPT-class clinical-error judge that counts six error categories at two severity tiers) and take a 5-vote majority with a fixed pass threshold of 3/5 zero-significant-error votes. The diagnostic `mean_sig_errors` is reported alongside binary pass rate so models that "fail less badly" are distinguishable from those that fail catastrophically.
8. **Two-service docker-compose with credential isolation.** The `bootstrap` service has PhysioNet creds, downloads on cache miss, and writes into shared volumes. The `main` service (where the agent runs) has *no* PN creds and the gold report is never bind-mounted into it. The verifier reads the gold from a separate `/tests/` mount at scoring time only.

## Upstream Runtime Notes

At read-date April 16, 2026:

- `mimic-cxr-reports.zip` on PhysioNet contains one `.txt` per study at `files/pXX/p<subject>/s<study>.txt`. Used for gold FINDINGS extraction.
- `mimic-cxr-jpg` v2.1.0 uses the same tree under `files/pXX/p<subject>/s<study>/<dicom>.jpg`.
- The split file `mimic-cxr-2.0.0-split.csv.gz` (shared between CXR and CXR-JPG) is used only at curation time; the 10 hand-picked cases bypass split-based filtering.
- `mimic-cxr-2.0.0-metadata.csv.gz` (~17 MB compressed, 377k rows) drives the prior-study enumeration.
- CheXprompt is installed inside a verifier-only venv (`/opt/verifier-venv`) with `chexprompt` + pinned `openai==0.28` (CheXprompt's expected SDK shape). The agent's venv never has CheXprompt or OpenAI credentials.
- CheXprompt judge defaults to `gpt-5.4` (overridable via `CHEXPROMPT_DEPLOYMENT` / `AZURE_OPENAI_DEPLOYMENT`). Works with vanilla OpenAI (`OPENAI_API_KEY` + `OPENAI_BASE_URL`) or Azure OpenAI (`AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_BASE_URL` + `AZURE_OPENAI_API_VERSION`); aliases handled in `harbor_evaluator._configure_openai_for_chexprompt`.

## Implications for This Repository

1. First multimodal, generative task in the MedCLI suite.
2. Task-level artifacts under `tasks/xray_report_correction/case_01..case_10/`; assets cache under `scripts/xray_report_correction/assets/` (gitignored); job configs at `jobs/xray_report_correction.yaml` (full 10-case) and `jobs/xray_report_correction_smoke.yaml` (2-case smoke).
3. Establishes the **two-service compose pattern with credential isolation** as the canonical shape for credentialed-download benchmarks (also used by `ct_abnormality` and `ehrshot`).
4. Establishes a **binary-reward + diagnostic-metric** convention: per-trial `reward.json` has flat `{reward, n_tasks, n_pass, pass_rate, mean_sig_errors}`; the `uv-script` aggregator pools to `{reward (= pass rate), success, n_trials, n_failed, mean_pass_rate, mean_sig_errors}`. Synthetic-zero rows are emitted for trials with `exception.txt`/`result.json` but no `reward.json`, so timeouts and crashes count against pass rate honestly.
5. The verifier raises a structured `MissingGoldError` when `/tests/target_report.txt` is absent or empty — this surfaces in Harbor's `exception_stats` rather than silently scoring 0, making it easy to distinguish bootstrap/environment failures from real agent failures.
