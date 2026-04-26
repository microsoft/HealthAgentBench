# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17327592`
- 3 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `59568059`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53734902
- **Date:** 2165-04-19 13:44:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2165-04-19_13-44-03_s53734902/`
- **Report:** `/data/patient/2165-04-19_13-44-03_s53734902/report.txt`
- **Images:** `/data/patient/2165-04-19_13-44-03_s53734902/d43e3c28-8d1a4b0c-ef446460-413e4e0b-df3a80ef.jpg`

### Prior Study 2: 51857131
- **Date:** 2166-03-30 10:53:08
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2166-03-30_10-53-08_s51857131/`
- **Report:** `/data/patient/2166-03-30_10-53-08_s51857131/report.txt`
- **Images:** `/data/patient/2166-03-30_10-53-08_s51857131/0b7e50b5-e294c033-a6ba8608-9ef1d9cf-16a24354.jpg`, `/data/patient/2166-03-30_10-53-08_s51857131/23f44245-c3dac2e5-2fe37a44-0f33bdee-fb440ccf.jpg`

### Prior Study 3: 52874049
- **Date:** 2168-03-24 20:46:14
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2168-03-24_20-46-14_s52874049/`
- **Report:** `/data/patient/2168-03-24_20-46-14_s52874049/report.txt`
- **Images:** `/data/patient/2168-03-24_20-46-14_s52874049/a67e2e2b-c5902ccf-adf291f3-51b417af-5b71eeaa.jpg`, `/data/patient/2168-03-24_20-46-14_s52874049/c90d5371-a8f60243-4bba58f2-aa0936cb-17473f87.jpg`

## Target Study

- **Study ID:** 59568059
- **Date:** 2168-04-13 11:47:25
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2168-04-13_11-47-25_s59568059/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2168-04-13_11-47-25_s59568059/0edc4350-79bed040-c995383a-424e4573-a701ab07.jpg`, `/data/patient/2168-04-13_11-47-25_s59568059/a163cafe-64ffc35b-319d99b1-4a167e5b-fff059e0.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PA AND LAT)

**INDICATION:** ___F with chest pain.

**COMPARISON:** ___

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