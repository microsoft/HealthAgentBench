# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12074041`
- 9 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51988570`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54973829
- **Date:** 2184-04-18 19:12:17
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2184-04-18_19-12-17_s54973829/`
- **Report:** `/data/patient/2184-04-18_19-12-17_s54973829/report.txt`
- **Images:** `/data/patient/2184-04-18_19-12-17_s54973829/a194aa87-2cb7c882-7602c814-7712dbb4-9ac8dea7.jpg`, `/data/patient/2184-04-18_19-12-17_s54973829/f430ec0f-40b790de-a5178baf-9dd6c108-9fc32de6.jpg`

### Prior Study 2: 52874646
- **Date:** 2184-04-30 17:01:24
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2184-04-30_17-01-24_s52874646/`
- **Report:** `/data/patient/2184-04-30_17-01-24_s52874646/report.txt`
- **Images:** `/data/patient/2184-04-30_17-01-24_s52874646/af39d55c-0622bc39-b9865798-29ff5a61-eb7cfb93.jpg`

### Prior Study 3: 54624512
- **Date:** 2184-05-01 05:18:13
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2184-05-01_05-18-13_s54624512/`
- **Report:** `/data/patient/2184-05-01_05-18-13_s54624512/report.txt`
- **Images:** `/data/patient/2184-05-01_05-18-13_s54624512/d91f5a1b-ccae5866-ec492d00-03828bba-bedd8a19.jpg`

### Prior Study 4: 56502688
- **Date:** 2184-11-17 16:04:15
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2184-11-17_16-04-15_s56502688/`
- **Report:** `/data/patient/2184-11-17_16-04-15_s56502688/report.txt`
- **Images:** `/data/patient/2184-11-17_16-04-15_s56502688/765fd687-06776030-fe337975-2739eab4-decbb9c2.jpg`

### Prior Study 5: 57679936
- **Date:** 2184-11-18 08:00:16
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2184-11-18_08-00-16_s57679936/`
- **Report:** `/data/patient/2184-11-18_08-00-16_s57679936/report.txt`
- **Images:** `/data/patient/2184-11-18_08-00-16_s57679936/467d9162-e7cce16e-70dfaa79-1867728f-1db6394e.jpg`

### Prior Study 6: 53353190
- **Date:** 2184-11-19 08:21:10
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2184-11-19_08-21-10_s53353190/`
- **Report:** `/data/patient/2184-11-19_08-21-10_s53353190/report.txt`
- **Images:** `/data/patient/2184-11-19_08-21-10_s53353190/172a847d-d8c6570a-3cb0cff9-cb4ca0bd-3a8b93f1.jpg`

### Prior Study 7: 53840157
- **Date:** 2184-11-28 14:56:25
- **Procedure:** Performed Desc
- **Views:** LL, LL, PA
- **Folder:** `/data/patient/2184-11-28_14-56-25_s53840157/`
- **Report:** `/data/patient/2184-11-28_14-56-25_s53840157/report.txt`
- **Images:** `/data/patient/2184-11-28_14-56-25_s53840157/807c53b9-9e9a06d2-201c5941-deae8153-ec887b70.jpg`, `/data/patient/2184-11-28_14-56-25_s53840157/db66ef84-840a9cf7-58eb1d86-97e44130-e32682cb.jpg`, `/data/patient/2184-11-28_14-56-25_s53840157/ebfa6753-3f0b7933-ca42ef98-0ce8ca94-b03f6676.jpg`

### Prior Study 8: 52969052
- **Date:** 2184-11-28 05:16:29
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2184-11-28_05-16-29_s52969052/`
- **Report:** `/data/patient/2184-11-28_05-16-29_s52969052/report.txt`
- **Images:** `/data/patient/2184-11-28_05-16-29_s52969052/b4a1b5bb-c12e1164-ded8460a-ccc5b283-abc72a43.jpg`

### Prior Study 9: 56121920
- **Date:** 2185-01-14 14:09:04
- **Procedure:** 
- **Views:** AP
- **Folder:** `/data/patient/2185-01-14_14-09-04_s56121920/`
- **Report:** `/data/patient/2185-01-14_14-09-04_s56121920/report.txt`
- **Images:** `/data/patient/2185-01-14_14-09-04_s56121920/d834b686-fc38fc45-187ea122-4e655952-20a720bd.jpg`

## Target Study

- **Study ID:** 51988570
- **Date:** 2185-02-23 15:00:30
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2185-02-23_15-00-30_s51988570/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2185-02-23_15-00-30_s51988570/a2f93b13-6b7f3079-3610454c-347f5e93-ad8f103b.jpg`, `/data/patient/2185-02-23_15-00-30_s51988570/c826aa5d-6ff5ee3a-11a18fb2-ab264bed-566e1edb.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

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