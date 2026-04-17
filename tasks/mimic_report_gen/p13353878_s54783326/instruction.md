# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13353878`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54783326`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59947192
- **Date:** 2188-05-07 05:37:10
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2188-05-07_05-37-10_s59947192/`
- **Report:** `/data/patient/2188-05-07_05-37-10_s59947192/report.txt`
- **Images:** `/data/patient/2188-05-07_05-37-10_s59947192/a2385584-b046d533-d61a4f1c-28a38feb-2aef2b6c.jpg`

### Prior Study 2: 56538372
- **Date:** 2188-05-09 19:07:58
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2188-05-09_19-07-58_s56538372/`
- **Report:** `/data/patient/2188-05-09_19-07-58_s56538372/report.txt`
- **Images:** `/data/patient/2188-05-09_19-07-58_s56538372/38fd10a6-9bc66421-6001dcd9-d1906370-18d01e97.jpg`, `/data/patient/2188-05-09_19-07-58_s56538372/fd7bea13-e6c0a9a2-06f163ea-d66e7a42-60a4dacb.jpg`

### Prior Study 3: 57540712
- **Date:** 2189-04-15 20:06:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2189-04-15_20-06-46_s57540712/`
- **Report:** `/data/patient/2189-04-15_20-06-46_s57540712/report.txt`
- **Images:** `/data/patient/2189-04-15_20-06-46_s57540712/8d70fba4-2de961f9-f5a521bd-99e41c4c-65e750ba.jpg`, `/data/patient/2189-04-15_20-06-46_s57540712/e90de45f-b12a6a45-721981dc-7df46eae-aa3318e1.jpg`

### Prior Study 4: 56510605
- **Date:** 2189-11-18 16:34:17
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2189-11-18_16-34-17_s56510605/`
- **Report:** `/data/patient/2189-11-18_16-34-17_s56510605/report.txt`
- **Images:** `/data/patient/2189-11-18_16-34-17_s56510605/c5d72977-09300b2f-a22239ad-2c5d50c8-0cc06cf6.jpg`, `/data/patient/2189-11-18_16-34-17_s56510605/c8186106-21770457-b7245fc6-d47e6b43-e07991e8.jpg`

## Target Study

- **Study ID:** 54783326
- **Date:** 2190-03-25 14:08:06
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, LATERAL
- **Folder:** `/data/patient/2190-03-25_14-08-06_s54783326/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2190-03-25_14-08-06_s54783326/1a81259c-493d3b3c-de7e0965-b13a0f4c-d813d91d.jpg`, `/data/patient/2190-03-25_14-08-06_s54783326/870c3a6b-22260d8a-f0ecaac8-e6be45f3-8789795e.jpg`, `/data/patient/2190-03-25_14-08-06_s54783326/8e4f1e80-f399aae7-0d76204f-8cb99fb9-e837fe04.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** ___-year-old female with chest pain.  Question pneumonia.

**COMPARISON:** ___.

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