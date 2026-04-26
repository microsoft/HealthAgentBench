# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17206933`
- 3 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51664027`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 56118817
- **Date:** 2127-10-23 18:19:47
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2127-10-23_18-19-47_s56118817/`
- **Report:** `/data/patient/2127-10-23_18-19-47_s56118817/report.txt`
- **Images:** `/data/patient/2127-10-23_18-19-47_s56118817/0a48d5b4-3f3aff93-e685c884-b13d2c6c-2c2ab46b.jpg`, `/data/patient/2127-10-23_18-19-47_s56118817/0d8df022-66df2226-6da5ef33-008b9273-022fa7f7.jpg`

### Prior Study 2: 57141526
- **Date:** 2127-11-06 18:31:54
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2127-11-06_18-31-54_s57141526/`
- **Report:** `/data/patient/2127-11-06_18-31-54_s57141526/report.txt`
- **Images:** `/data/patient/2127-11-06_18-31-54_s57141526/09c510a6-55f47c1d-504f429b-f333cf7f-7ccf6ac6.jpg`, `/data/patient/2127-11-06_18-31-54_s57141526/ec72dd86-36c802f0-20a909ca-8cbcc950-58733cd5.jpg`

### Prior Study 3: 57571408
- **Date:** 2127-11-08 08:39:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2127-11-08_08-39-03_s57571408/`
- **Report:** `/data/patient/2127-11-08_08-39-03_s57571408/report.txt`
- **Images:** `/data/patient/2127-11-08_08-39-03_s57571408/42ca3426-3c2dc573-7e2d42fe-aa2b9627-d888b47b.jpg`

## Target Study

- **Study ID:** 51664027
- **Date:** 2127-11-25 02:16:40
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2127-11-25_02-16-40_s51664027/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2127-11-25_02-16-40_s51664027/ff6e7a7d-9a6dcd6f-295e7a94-b49fbcc3-502bd3ab.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Hypoxia with shortness of breath.  Evaluate for CHF, pneumonia,
 and/or effusions.

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