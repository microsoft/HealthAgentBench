# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `10274145`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `53356050`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58307391
- **Date:** 2174-06-01 19:37:22
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2174-06-01_19-37-22_s58307391/`
- **Report:** `/data/patient/2174-06-01_19-37-22_s58307391/report.txt`
- **Images:** `/data/patient/2174-06-01_19-37-22_s58307391/638f2c7f-1ddfe2c3-062f8057-b3e8a5aa-17b03955.jpg`, `/data/patient/2174-06-01_19-37-22_s58307391/b863ce69-7e0670b3-3c5a3a29-b96b7248-a616113c.jpg`

### Prior Study 2: 53183707
- **Date:** 2174-06-04 15:46:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , LL
- **Folder:** `/data/patient/2174-06-04_15-46-46_s53183707/`
- **Report:** `/data/patient/2174-06-04_15-46-46_s53183707/report.txt`
- **Images:** `/data/patient/2174-06-04_15-46-46_s53183707/d570aba7-45a558d7-52f77673-704bdc98-85e97946.jpg`, `/data/patient/2174-06-04_15-46-46_s53183707/d6051124-a16053dc-2b4ecb89-8e1a17a9-252c1e8f.jpg`

### Prior Study 3: 56140866
- **Date:** 2174-06-10 10:02:46
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2174-06-10_10-02-46_s56140866/`
- **Report:** `/data/patient/2174-06-10_10-02-46_s56140866/report.txt`
- **Images:** `/data/patient/2174-06-10_10-02-46_s56140866/515cb0a1-2209cb99-b1f8292c-d6d6acc1-1533f233.jpg`, `/data/patient/2174-06-10_10-02-46_s56140866/7b43b8ff-190d3ca9-03cfbbd3-45ad3d0d-72d06c1c.jpg`

### Prior Study 4: 59166131
- **Date:** 2174-06-11 10:14:18
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2174-06-11_10-14-18_s59166131/`
- **Report:** `/data/patient/2174-06-11_10-14-18_s59166131/report.txt`
- **Images:** `/data/patient/2174-06-11_10-14-18_s59166131/29ab48f7-15a14464-5b7c1cc3-3ba3aa97-64ebc637.jpg`, `/data/patient/2174-06-11_10-14-18_s59166131/2cc38dd6-d1f5970f-055155bc-e9e8fccd-8ec98168.jpg`

## Target Study

- **Study ID:** 53356050
- **Date:** 2174-08-25 03:49:02
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP, LATERAL
- **Folder:** `/data/patient/2174-08-25_03-49-02_s53356050/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2174-08-25_03-49-02_s53356050/4a0397d2-1c7cac8d-bd1e1991-d3459191-3e510506.jpg`, `/data/patient/2174-08-25_03-49-02_s53356050/4e60f3da-37ed157d-a469a568-0b2ee907-4b01c924.jpg`, `/data/patient/2174-08-25_03-49-02_s53356050/8f25d878-fb6e48eb-adfc39cb-10da1ebd-3d14c369.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Erratic blood sugars.  Please evaluate for pneumonia.

**COMPARISON:** Comparison is made to chest radiograph performed ___.

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