# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17288844`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54644366`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53298293
- **Date:** 2197-08-29 13:51:47
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2197-08-29_13-51-47_s53298293/`
- **Report:** `/data/patient/2197-08-29_13-51-47_s53298293/report.txt`
- **Images:** `/data/patient/2197-08-29_13-51-47_s53298293/c6b71b77-d56881b6-ee8c63bc-6ee0be88-89856367.jpg`

### Prior Study 2: 52481016
- **Date:** 2197-08-29 02:52:36
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2197-08-29_02-52-36_s52481016/`
- **Report:** `/data/patient/2197-08-29_02-52-36_s52481016/report.txt`
- **Images:** `/data/patient/2197-08-29_02-52-36_s52481016/c57c824d-1eddb1d5-5933f11b-3da0b20b-0bd14eef.jpg`

### Prior Study 3: 51904170
- **Date:** 2197-08-30 07:43:34
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2197-08-30_07-43-34_s51904170/`
- **Report:** `/data/patient/2197-08-30_07-43-34_s51904170/report.txt`
- **Images:** `/data/patient/2197-08-30_07-43-34_s51904170/cf6229c4-0dbb5dd3-64610954-17ed414a-c7d2837d.jpg`

### Prior Study 4: 52302794
- **Date:** 2197-08-31 08:23:40
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2197-08-31_08-23-40_s52302794/`
- **Report:** `/data/patient/2197-08-31_08-23-40_s52302794/report.txt`
- **Images:** `/data/patient/2197-08-31_08-23-40_s52302794/e12f3c50-f3483123-b58a8f99-6e949bb7-98729b1a.jpg`

### Prior Study 5: 53092956
- **Date:** 2197-09-01 07:33:32
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2197-09-01_07-33-32_s53092956/`
- **Report:** `/data/patient/2197-09-01_07-33-32_s53092956/report.txt`
- **Images:** `/data/patient/2197-09-01_07-33-32_s53092956/930dd047-b21f81bf-197ca30e-463d627b-aedbcdc3.jpg`

## Target Study

- **Study ID:** 54644366
- **Date:** 2197-09-02 01:01:24
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2197-09-02_01-01-24_s54644366/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2197-09-02_01-01-24_s54644366/adcf4325-aa59cd31-be329869-32fd0147-d3cd1387.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** ___-year-old male status post STEMI, now with new oxygen
 desaturations.
 
 STUDY:  Semi-erect portable AP chest radiograph.

**COMPARISON:** Multiple chest radiographs from ___ through ___.

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