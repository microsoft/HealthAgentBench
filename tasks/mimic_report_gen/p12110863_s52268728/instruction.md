# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12110863`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `52268728`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59358922
- **Date:** 2155-08-21 01:25:29
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2155-08-21_01-25-29_s59358922/`
- **Report:** `/data/patient/2155-08-21_01-25-29_s59358922/report.txt`
- **Images:** `/data/patient/2155-08-21_01-25-29_s59358922/1e63fbae-cd836c8c-60c8d534-08ef62b9-a33e82f2.jpg`, `/data/patient/2155-08-21_01-25-29_s59358922/fba838cc-fa4eb8b6-b3e8de64-e89c00ab-1bb9216a.jpg`

### Prior Study 2: 55875120
- **Date:** 2155-09-19 01:06:06
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2155-09-19_01-06-06_s55875120/`
- **Report:** `/data/patient/2155-09-19_01-06-06_s55875120/report.txt`
- **Images:** `/data/patient/2155-09-19_01-06-06_s55875120/6f619231-f8a0ab48-6858a7eb-b0ee9c1c-de3385c9.jpg`, `/data/patient/2155-09-19_01-06-06_s55875120/c12759af-b70b6882-d6cca08e-8811c264-7caf797c.jpg`

### Prior Study 3: 50751429
- **Date:** 2155-09-19 03:23:14
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2155-09-19_03-23-14_s50751429/`
- **Report:** `/data/patient/2155-09-19_03-23-14_s50751429/report.txt`
- **Images:** `/data/patient/2155-09-19_03-23-14_s50751429/7568a044-7f2b130e-9af97f69-17cda54e-cb366755.jpg`

### Prior Study 4: 55498995
- **Date:** 2155-11-08 11:27:30
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2155-11-08_11-27-30_s55498995/`
- **Report:** `/data/patient/2155-11-08_11-27-30_s55498995/report.txt`
- **Images:** `/data/patient/2155-11-08_11-27-30_s55498995/e538135c-ebad1b7e-5f239803-3d6bcf94-7c5fddc4.jpg`

### Prior Study 5: 53008088
- **Date:** 2155-12-17 21:11:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2155-12-17_21-11-06_s53008088/`
- **Report:** `/data/patient/2155-12-17_21-11-06_s53008088/report.txt`
- **Images:** `/data/patient/2155-12-17_21-11-06_s53008088/22a06cfc-11fababd-02d9a890-42cbc80e-34757e33.jpg`

### Prior Study 6: 58379619
- **Date:** 2155-12-22 11:38:34
- **Procedure:** Performed Desc
- **Views:** LL, 
- **Folder:** `/data/patient/2155-12-22_11-38-34_s58379619/`
- **Report:** `/data/patient/2155-12-22_11-38-34_s58379619/report.txt`
- **Images:** `/data/patient/2155-12-22_11-38-34_s58379619/76d2e3a0-a3074ba0-1b66d561-1eb29b13-3bb093aa.jpg`, `/data/patient/2155-12-22_11-38-34_s58379619/9d53d4d6-3495e14a-d2f6c5b0-333b5174-8b65e1ab.jpg`

## Target Study

- **Study ID:** 52268728
- **Date:** 2156-03-09 18:47:48
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2156-03-09_18-47-48_s52268728/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2156-03-09_18-47-48_s52268728/67412cf5-519f1711-72f5a403-2e6ec7fa-84dfa6b6.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**COMPARISON:** ___ and CT chest from ___.
 
 CLINICAL HISTORY:  Cough, tachypnea, question pneumonia.

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