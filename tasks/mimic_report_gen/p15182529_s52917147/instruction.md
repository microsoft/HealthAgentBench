# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15182529`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `52917147`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 56993533
- **Date:** 2144-11-19 12:37:34
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2144-11-19_12-37-34_s56993533/`
- **Report:** `/data/patient/2144-11-19_12-37-34_s56993533/report.txt`
- **Images:** `/data/patient/2144-11-19_12-37-34_s56993533/c3827619-5b104baa-e1895045-007f9978-837ef55e.jpg`

### Prior Study 2: 57527174
- **Date:** 2144-11-21 09:46:00
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2144-11-21_09-46-00_s57527174/`
- **Report:** `/data/patient/2144-11-21_09-46-00_s57527174/report.txt`
- **Images:** `/data/patient/2144-11-21_09-46-00_s57527174/e26f890e-29d7bdec-2cd5238a-90a1a416-c07956de.jpg`, `/data/patient/2144-11-21_09-46-00_s57527174/e337d4c3-16ff3087-0094492f-365edc12-31b45f47.jpg`

## Target Study

- **Study ID:** 52917147
- **Date:** 2146-04-12 10:23:25
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2146-04-12_10-23-25_s52917147/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2146-04-12_10-23-25_s52917147/7095b09e-8fea76ab-f2c3c5aa-6c08e75a-0c451ac5.jpg`, `/data/patient/2146-04-12_10-23-25_s52917147/af7cf015-dffc91c8-acbf1261-5199a5eb-a18d71cf.jpg`, `/data/patient/2146-04-12_10-23-25_s52917147/c2402f4a-6c5552e7-e0b4749a-2b88ba69-f59a01a6.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** Worsening weakness with fall in shower 2 days ago and head injury.

**COMPARISON:** Comparison exam chest radiographs from ___ and ___.

## Your Task

Produce ONLY the FINDINGS and IMPRESSION sections of the target study's report.
Use the target study's images, the provided sections above, and the patient's
prior imaging history (reports + images in `/data/patient/`) as context.

Format your `final_answer` exactly as:

```
FINDINGS:
<your findings text>

IMPRESSION:
<your impression text>
```

Do NOT include EXAMINATION/INDICATION/TECHNIQUE/COMPARISON/HISTORY headers in
your answer — they are already part of the report and will be combined externally.

## Submission Rules

- Set `final_answer` to FINDINGS + IMPRESSION text only (free text)
- Do NOT modify `task_id` or `instruction` fields
- Work autonomously until the submission is complete

**IMPORTANT: update `submission.json` using a JSON-aware tool (e.g., `python -c "import json; ..."`),
NOT by editing the raw text. Manual string edits easily corrupt the JSON.**