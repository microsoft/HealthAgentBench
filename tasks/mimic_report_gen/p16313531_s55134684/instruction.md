# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `16313531`
- 10 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55134684`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58096693
- **Date:** 2145-03-06 15:47:27
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-06_15-47-27_s58096693/`
- **Report:** `/data/patient/2145-03-06_15-47-27_s58096693/report.txt`
- **Images:** `/data/patient/2145-03-06_15-47-27_s58096693/5df5745b-a26b6124-07ab0ff7-a79cf0ca-d84b7fa1.jpg`

### Prior Study 2: 58455247
- **Date:** 2145-03-07 18:17:58
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-07_18-17-58_s58455247/`
- **Report:** `/data/patient/2145-03-07_18-17-58_s58455247/report.txt`
- **Images:** `/data/patient/2145-03-07_18-17-58_s58455247/00c7d4e9-802b89b1-4bd840b3-e5fd2fc9-5d38566e.jpg`

### Prior Study 3: 51111527
- **Date:** 2145-03-08 12:13:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-08_12-13-03_s51111527/`
- **Report:** `/data/patient/2145-03-08_12-13-03_s51111527/report.txt`
- **Images:** `/data/patient/2145-03-08_12-13-03_s51111527/7d2c16b5-f6f795bc-48420b1a-415e3df8-8d442753.jpg`

### Prior Study 4: 52300884
- **Date:** 2145-03-09 12:47:31
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-09_12-47-31_s52300884/`
- **Report:** `/data/patient/2145-03-09_12-47-31_s52300884/report.txt`
- **Images:** `/data/patient/2145-03-09_12-47-31_s52300884/fe59a37b-153a2ffa-4552395e-09148941-f3badae1.jpg`

### Prior Study 5: 58147681
- **Date:** 2145-03-10 02:29:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-10_02-29-03_s58147681/`
- **Report:** `/data/patient/2145-03-10_02-29-03_s58147681/report.txt`
- **Images:** `/data/patient/2145-03-10_02-29-03_s58147681/8d361e7d-f4f46fc7-956ef2b6-bc506025-0df660c3.jpg`

### Prior Study 6: 57570449
- **Date:** 2145-03-11 02:18:41
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-11_02-18-41_s57570449/`
- **Report:** `/data/patient/2145-03-11_02-18-41_s57570449/report.txt`
- **Images:** `/data/patient/2145-03-11_02-18-41_s57570449/56a7703d-e485b8f2-cedb0b12-8138943c-86df9465.jpg`

### Prior Study 7: 55316723
- **Date:** 2145-03-13 00:58:54
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-13_00-58-54_s55316723/`
- **Report:** `/data/patient/2145-03-13_00-58-54_s55316723/report.txt`
- **Images:** `/data/patient/2145-03-13_00-58-54_s55316723/c8432be1-b79e41da-834ae99a-c6cd0b0f-414d4eec.jpg`

### Prior Study 8: 59994014
- **Date:** 2145-03-14 10:11:37
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-14_10-11-37_s59994014/`
- **Report:** `/data/patient/2145-03-14_10-11-37_s59994014/report.txt`
- **Images:** `/data/patient/2145-03-14_10-11-37_s59994014/605a5651-5fb67eb8-b56ccc7e-8fce40db-0924c841.jpg`

### Prior Study 9: 56699078
- **Date:** 2145-03-20 10:10:31
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-03-20_10-10-31_s56699078/`
- **Report:** `/data/patient/2145-03-20_10-10-31_s56699078/report.txt`
- **Images:** `/data/patient/2145-03-20_10-10-31_s56699078/efc15848-2e4788fd-35891eca-87c4c2a8-e9d28d15.jpg`

### Prior Study 10: 57149976
- **Date:** 2145-11-24 00:25:17
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2145-11-24_00-25-17_s57149976/`
- **Report:** `/data/patient/2145-11-24_00-25-17_s57149976/report.txt`
- **Images:** `/data/patient/2145-11-24_00-25-17_s57149976/9899772e-b051b74d-f68faa87-f45ebf9b-3fcd4d7b.jpg`

## Target Study

- **Study ID:** 55134684
- **Date:** 2145-11-29 11:14:12
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , LL
- **Folder:** `/data/patient/2145-11-29_11-14-12_s55134684/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2145-11-29_11-14-12_s55134684/583590d0-c9c3ce35-4b385739-1623390c-62fd1b5d.jpg`, `/data/patient/2145-11-29_11-14-12_s55134684/bcbe5ec6-d84ec5ad-7815dc90-92ca0882-48d3c3a6.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**COMPARISON:** Chest x-ray ___.

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