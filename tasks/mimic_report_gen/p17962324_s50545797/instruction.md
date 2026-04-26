# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17962324`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50545797`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 56599347
- **Date:** 2171-04-24 18:57:44
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2171-04-24_18-57-44_s56599347/`
- **Report:** `/data/patient/2171-04-24_18-57-44_s56599347/report.txt`
- **Images:** `/data/patient/2171-04-24_18-57-44_s56599347/2e25b67d-2fe26860-9bd31e83-0ae5d783-44e5bc1e.jpg`

### Prior Study 2: 58141612
- **Date:** 2171-04-26 18:36:49
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2171-04-26_18-36-49_s58141612/`
- **Report:** `/data/patient/2171-04-26_18-36-49_s58141612/report.txt`
- **Images:** `/data/patient/2171-04-26_18-36-49_s58141612/b5f871d3-8702f640-44c08eed-e1b45081-74211f61.jpg`

### Prior Study 3: 59875098
- **Date:** 2173-09-30 08:46:55
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2173-09-30_08-46-55_s59875098/`
- **Report:** `/data/patient/2173-09-30_08-46-55_s59875098/report.txt`
- **Images:** `/data/patient/2173-09-30_08-46-55_s59875098/2830f665-0aaa29d2-595be5a7-693ce7bf-c71d0c0b.jpg`, `/data/patient/2173-09-30_08-46-55_s59875098/9188d253-7432f199-b8668189-c4b015e6-24ed4f79.jpg`

### Prior Study 4: 50935375
- **Date:** 2173-11-16 12:02:59
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2173-11-16_12-02-59_s50935375/`
- **Report:** `/data/patient/2173-11-16_12-02-59_s50935375/report.txt`
- **Images:** `/data/patient/2173-11-16_12-02-59_s50935375/41df0913-e1804610-248fbdd1-6c00cbe1-01bebf5e.jpg`, `/data/patient/2173-11-16_12-02-59_s50935375/e7c283a2-7103747a-f58558d4-48c8259f-aeb043ac.jpg`

## Target Study

- **Study ID:** 50545797
- **Date:** 2174-09-09 19:11:29
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL, PA
- **Folder:** `/data/patient/2174-09-09_19-11-29_s50545797/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2174-09-09_19-11-29_s50545797/3a95996c-94c41329-d656550a-90424b30-ec861fcc.jpg`, `/data/patient/2174-09-09_19-11-29_s50545797/5ace239b-61b2f2f3-103b0d93-d3803c39-ef06ca44.jpg`, `/data/patient/2174-09-09_19-11-29_s50545797/c768ecd2-dec91075-b6e6d204-6a9d0da8-e1ce939a.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___M with h/o cad w/ dyspnea and hypoxia  // chf?

**TECHNIQUE:** PA and lateral views of the chest.

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