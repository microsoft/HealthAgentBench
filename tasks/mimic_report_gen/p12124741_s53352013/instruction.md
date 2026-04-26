# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12124741`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `53352013`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52680361
- **Date:** 2186-11-21 10:14:07
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2186-11-21_10-14-07_s52680361/`
- **Report:** `/data/patient/2186-11-21_10-14-07_s52680361/report.txt`
- **Images:** `/data/patient/2186-11-21_10-14-07_s52680361/415af9ca-d0b69fbe-b3b8dfa6-271f3f0f-5592cc53.jpg`

### Prior Study 2: 52979134
- **Date:** 2187-01-04 12:13:00
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2187-01-04_12-13-00_s52979134/`
- **Report:** `/data/patient/2187-01-04_12-13-00_s52979134/report.txt`
- **Images:** `/data/patient/2187-01-04_12-13-00_s52979134/0b53daa0-d9ca6166-9622edee-57037ea3-8a1bf264.jpg`, `/data/patient/2187-01-04_12-13-00_s52979134/e53b12a2-325afb40-3283ac75-9f92dfc7-5e579ec0.jpg`, `/data/patient/2187-01-04_12-13-00_s52979134/ebf694d1-74d14ed6-c1695437-a0c9b0f3-cb905ce8.jpg`

### Prior Study 3: 53809636
- **Date:** 2187-01-08 11:50:43
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2187-01-08_11-50-43_s53809636/`
- **Report:** `/data/patient/2187-01-08_11-50-43_s53809636/report.txt`
- **Images:** `/data/patient/2187-01-08_11-50-43_s53809636/1360763e-71ee973d-a29d16c9-9763397e-37844701.jpg`

### Prior Study 4: 57169558
- **Date:** 2187-01-08 00:33:33
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2187-01-08_00-33-33_s57169558/`
- **Report:** `/data/patient/2187-01-08_00-33-33_s57169558/report.txt`
- **Images:** `/data/patient/2187-01-08_00-33-33_s57169558/7ceecc91-32932b6b-bf0ae761-92a74cf7-fe124fbc.jpg`

### Prior Study 5: 55477134
- **Date:** 2187-01-09 14:41:41
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2187-01-09_14-41-41_s55477134/`
- **Report:** `/data/patient/2187-01-09_14-41-41_s55477134/report.txt`
- **Images:** `/data/patient/2187-01-09_14-41-41_s55477134/b057552d-dcaef0e0-258a2453-37c600b2-d8d2b31f.jpg`

### Prior Study 6: 57320234
- **Date:** 2187-01-12 09:51:22
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2187-01-12_09-51-22_s57320234/`
- **Report:** `/data/patient/2187-01-12_09-51-22_s57320234/report.txt`
- **Images:** `/data/patient/2187-01-12_09-51-22_s57320234/43b4627a-0c31cd6a-92c2144b-ecbf51e1-1519741b.jpg`, `/data/patient/2187-01-12_09-51-22_s57320234/72a15dc0-cfcca17f-201baf20-76f2e298-e4123143.jpg`

## Target Study

- **Study ID:** 53352013
- **Date:** 2187-11-20 14:16:14
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2187-11-20_14-16-14_s53352013/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2187-11-20_14-16-14_s53352013/783fc94d-12b747b1-600f2e10-c1c51d2a-97240f95.jpg`, `/data/patient/2187-11-20_14-16-14_s53352013/ebd066f6-f32177f2-c211270d-aeb7bae8-f4b6d9a2.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**COMPARISON:** ___.
 
 CLINICAL HISTORY:  Chest pain.

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