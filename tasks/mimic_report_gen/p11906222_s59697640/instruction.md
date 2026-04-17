# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `11906222`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `59697640`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53854854
- **Date:** 2148-06-03 16:08:59
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2148-06-03_16-08-59_s53854854/`
- **Report:** `/data/patient/2148-06-03_16-08-59_s53854854/report.txt`
- **Images:** `/data/patient/2148-06-03_16-08-59_s53854854/567bcd19-6ab220b4-8f8eb57b-5f94b009-a4007fc7.jpg`

### Prior Study 2: 57232140
- **Date:** 2148-06-06 17:13:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2148-06-06_17-13-06_s57232140/`
- **Report:** `/data/patient/2148-06-06_17-13-06_s57232140/report.txt`
- **Images:** `/data/patient/2148-06-06_17-13-06_s57232140/42e634b1-94de1686-ecd12cab-6619202e-8694c45c.jpg`, `/data/patient/2148-06-06_17-13-06_s57232140/64927291-fe42a66c-af054049-3d17501b-5de4163c.jpg`

### Prior Study 3: 55124994
- **Date:** 2148-06-11 07:00:55
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2148-06-11_07-00-55_s55124994/`
- **Report:** `/data/patient/2148-06-11_07-00-55_s55124994/report.txt`
- **Images:** `/data/patient/2148-06-11_07-00-55_s55124994/a7b100cd-08c2be2d-a32c2dac-020c1d75-1bd5b887.jpg`

### Prior Study 4: 56779415
- **Date:** 2148-06-12 03:52:53
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2148-06-12_03-52-53_s56779415/`
- **Report:** `/data/patient/2148-06-12_03-52-53_s56779415/report.txt`
- **Images:** `/data/patient/2148-06-12_03-52-53_s56779415/345c27ae-8dc96bd7-cd59fd7f-e18c90bc-71bf8122.jpg`

### Prior Study 5: 52008677
- **Date:** 2148-09-20 11:16:33
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2148-09-20_11-16-33_s52008677/`
- **Report:** `/data/patient/2148-09-20_11-16-33_s52008677/report.txt`
- **Images:** `/data/patient/2148-09-20_11-16-33_s52008677/59a291bb-a5b73755-8efc4039-1a4e13f2-887e46d2.jpg`, `/data/patient/2148-09-20_11-16-33_s52008677/b6a2b75a-2f7feeff-1e47f4d0-1d86b2ff-c5d8d6c1.jpg`

## Target Study

- **Study ID:** 59697640
- **Date:** 2148-11-27 11:44:47
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, LATERAL
- **Folder:** `/data/patient/2148-11-27_11-44-47_s59697640/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2148-11-27_11-44-47_s59697640/20ae33e5-c3a0b30d-d737101f-b47e9ae1-d804765a.jpg`, `/data/patient/2148-11-27_11-44-47_s59697640/efc879d0-ba7f1b53-560419c8-f53bda85-6bd62bb3.jpg`, `/data/patient/2148-11-27_11-44-47_s59697640/f9e14eb7-74cf98e3-62e6bf8d-4c92c03f-b22373f6.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Syncope.  Assess for acute cardiac or pulmonary process.

**COMPARISON:** Chest radiograph from ___.

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