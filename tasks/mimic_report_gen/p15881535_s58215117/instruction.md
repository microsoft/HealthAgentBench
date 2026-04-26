# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15881535`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `58215117`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 56093476
- **Date:** 2185-08-09 14:01:41
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP
- **Folder:** `/data/patient/2185-08-09_14-01-41_s56093476/`
- **Report:** `/data/patient/2185-08-09_14-01-41_s56093476/report.txt`
- **Images:** `/data/patient/2185-08-09_14-01-41_s56093476/210f9c01-9e0728bf-4b8ec9bf-34d1564e-16cf509c.jpg`

### Prior Study 2: 58897728
- **Date:** 2189-02-21 23:28:15
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2189-02-21_23-28-15_s58897728/`
- **Report:** `/data/patient/2189-02-21_23-28-15_s58897728/report.txt`
- **Images:** `/data/patient/2189-02-21_23-28-15_s58897728/19c60eb8-3699971f-b058c7f4-9032d4a4-2b586b3f.jpg`, `/data/patient/2189-02-21_23-28-15_s58897728/7fae1179-39697856-a9795bb4-19feb4f6-b065f924.jpg`

## Target Study

- **Study ID:** 58215117
- **Date:** 2189-12-17 16:12:58
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2189-12-17_16-12-58_s58215117/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2189-12-17_16-12-58_s58215117/5b544b50-6b9fd2e8-40331062-6eea2423-c6427c30.jpg`, `/data/patient/2189-12-17_16-12-58_s58215117/5fdb7189-ead5e2fd-71a6d19b-3862ce63-28bc762e.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** Chest PA and lateral.

**INDICATION:** ___-year-old man with cough for 4 weeks. Evaluate for pneumonia.

**TECHNIQUE:** Chest PA and lateral.

**COMPARISON:** Multiple prior chest radiographs, most recent from ___.

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