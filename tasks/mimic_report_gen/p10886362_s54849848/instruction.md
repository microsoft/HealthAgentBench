# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `10886362`
- 9 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54849848`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52555178
- **Date:** 2135-02-08 05:14:00
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2135-02-08_05-14-00_s52555178/`
- **Report:** `/data/patient/2135-02-08_05-14-00_s52555178/report.txt`
- **Images:** `/data/patient/2135-02-08_05-14-00_s52555178/5fd6fa4a-2108246f-d9199b99-e14370ae-0eea894d.jpg`

### Prior Study 2: 58072789
- **Date:** 2135-03-03 18:36:44
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2135-03-03_18-36-44_s58072789/`
- **Report:** `/data/patient/2135-03-03_18-36-44_s58072789/report.txt`
- **Images:** `/data/patient/2135-03-03_18-36-44_s58072789/0b7ab545-c2af9860-5aae88b7-7e27fa66-b0c115db.jpg`, `/data/patient/2135-03-03_18-36-44_s58072789/22626212-038a564e-86e62d8b-9d61ea9c-daa48afc.jpg`

### Prior Study 3: 53460154
- **Date:** 2135-03-04 10:32:45
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2135-03-04_10-32-45_s53460154/`
- **Report:** `/data/patient/2135-03-04_10-32-45_s53460154/report.txt`
- **Images:** `/data/patient/2135-03-04_10-32-45_s53460154/b4391db8-8076224b-e326c566-f0ee0cd4-94341441.jpg`

### Prior Study 4: 54962274
- **Date:** 2135-03-04 20:45:17
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2135-03-04_20-45-17_s54962274/`
- **Report:** `/data/patient/2135-03-04_20-45-17_s54962274/report.txt`
- **Images:** `/data/patient/2135-03-04_20-45-17_s54962274/51dc7b8e-860b2222-aad3c79e-02a2a9d0-085ebd6d.jpg`, `/data/patient/2135-03-04_20-45-17_s54962274/68ea99a4-bd75cd2b-df54e0c2-ae1f3e13-c5a9bca4.jpg`

### Prior Study 5: 57211901
- **Date:** 2135-03-04 09:19:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2135-03-04_09-19-18_s57211901/`
- **Report:** `/data/patient/2135-03-04_09-19-18_s57211901/report.txt`
- **Images:** `/data/patient/2135-03-04_09-19-18_s57211901/c5317373-5acdf384-4d5fee0f-423f29ef-22858502.jpg`

### Prior Study 6: 55957472
- **Date:** 2135-03-04 09:59:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2135-03-04_09-59-06_s55957472/`
- **Report:** `/data/patient/2135-03-04_09-59-06_s55957472/report.txt`
- **Images:** `/data/patient/2135-03-04_09-59-06_s55957472/10de7e37-6e13bc83-6797db44-6cac4fdb-8bcba198.jpg`, `/data/patient/2135-03-04_09-59-06_s55957472/b2b5a3a4-24b4dc24-84c9e1a5-98f8a217-8c89ba2a.jpg`

### Prior Study 7: 50301215
- **Date:** 2135-03-05 11:55:48
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2135-03-05_11-55-48_s50301215/`
- **Report:** `/data/patient/2135-03-05_11-55-48_s50301215/report.txt`
- **Images:** `/data/patient/2135-03-05_11-55-48_s50301215/104737c6-53b91029-bb16816d-13bbcdb8-0564caa2.jpg`, `/data/patient/2135-03-05_11-55-48_s50301215/60c60c6e-1471b41d-d8ae011a-299592ea-7c39d5e7.jpg`

### Prior Study 8: 51423353
- **Date:** 2135-03-05 17:58:13
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2135-03-05_17-58-13_s51423353/`
- **Report:** `/data/patient/2135-03-05_17-58-13_s51423353/report.txt`
- **Images:** `/data/patient/2135-03-05_17-58-13_s51423353/9192ac1a-8d64bbf3-4b035831-96f59abc-903b2aaa.jpg`

### Prior Study 9: 56034024
- **Date:** 2135-03-06 15:27:28
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2135-03-06_15-27-28_s56034024/`
- **Report:** `/data/patient/2135-03-06_15-27-28_s56034024/report.txt`
- **Images:** `/data/patient/2135-03-06_15-27-28_s56034024/fdd8adcf-96e61323-ef98915c-c91ab8b9-7bf45f5e.jpg`

## Target Study

- **Study ID:** 54849848
- **Date:** 2135-03-10 12:09:08
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2135-03-10_12-09-08_s54849848/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2135-03-10_12-09-08_s54849848/9189763d-c3b6ee12-d0d89f14-29a0cb1f-e3dee331.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old male patient with hypoxia, evaluate for radiologic
 evidence of hypoxia.

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