# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13762730`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54472974`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 50664785
- **Date:** 2139-05-14 00:42:33
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2139-05-14_00-42-33_s50664785/`
- **Report:** `/data/patient/2139-05-14_00-42-33_s50664785/report.txt`
- **Images:** `/data/patient/2139-05-14_00-42-33_s50664785/db39cf32-d22fb990-e46ba7c8-c73f9b0b-c77db2a1.jpg`

### Prior Study 2: 55828202
- **Date:** 2139-05-18 10:22:42
- **Procedure:** 
- **Views:** PA
- **Folder:** `/data/patient/2139-05-18_10-22-42_s55828202/`
- **Report:** `/data/patient/2139-05-18_10-22-42_s55828202/report.txt`
- **Images:** `/data/patient/2139-05-18_10-22-42_s55828202/428c4099-c29bb97d-e06be8f3-614d3b6e-d343eee7.jpg`

### Prior Study 3: 58807210
- **Date:** 2139-09-22 08:39:36
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2139-09-22_08-39-36_s58807210/`
- **Report:** `/data/patient/2139-09-22_08-39-36_s58807210/report.txt`
- **Images:** `/data/patient/2139-09-22_08-39-36_s58807210/49177e16-0383da48-c2a81ed9-77e7a7c0-bbe8c9cb.jpg`, `/data/patient/2139-09-22_08-39-36_s58807210/e3555bac-cb4ffa77-657be5f9-38bcdc9b-0b46292b.jpg`

### Prior Study 4: 52603243
- **Date:** 2139-09-25 08:15:15
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2139-09-25_08-15-15_s52603243/`
- **Report:** `/data/patient/2139-09-25_08-15-15_s52603243/report.txt`
- **Images:** `/data/patient/2139-09-25_08-15-15_s52603243/1122a7e9-32e0350f-1a87fedd-c85128f3-4e2d23f4.jpg`, `/data/patient/2139-09-25_08-15-15_s52603243/41da5168-3827dda7-50545888-b2a593ef-1dd0934d.jpg`, `/data/patient/2139-09-25_08-15-15_s52603243/ea8f47d3-a878270a-7a5e0d98-b1d62b7e-6061c574.jpg`

## Target Study

- **Study ID:** 54472974
- **Date:** 2140-10-26 18:58:39
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2140-10-26_18-58-39_s54472974/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2140-10-26_18-58-39_s54472974/0ff0bb39-4a3b9b22-0150d88d-040cd9e6-c1d6078b.jpg`, `/data/patient/2140-10-26_18-58-39_s54472974/93795e56-ef882771-fa23c36d-bf8cf35b-fc41aadc.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**COMPARISON:** ___ radiograph.

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