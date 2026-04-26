# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14081759`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50184397`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53482917
- **Date:** 2152-02-26 14:48:10
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2152-02-26_14-48-10_s53482917/`
- **Report:** `/data/patient/2152-02-26_14-48-10_s53482917/report.txt`
- **Images:** `/data/patient/2152-02-26_14-48-10_s53482917/291ce527-905f8ce6-f01b0fd5-c7a6f3bb-c126f711.jpg`, `/data/patient/2152-02-26_14-48-10_s53482917/4d69cce1-fecc3019-ee62f6c0-dc12a81e-ae02844a.jpg`

### Prior Study 2: 52995335
- **Date:** 2152-02-26 19:45:23
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-02-26_19-45-23_s52995335/`
- **Report:** `/data/patient/2152-02-26_19-45-23_s52995335/report.txt`
- **Images:** `/data/patient/2152-02-26_19-45-23_s52995335/b3281e41-ce38300f-dce229b7-74d8e99e-aac1c9c5.jpg`

## Target Study

- **Study ID:** 50184397
- **Date:** 2152-03-20 18:43:52
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, LATERAL
- **Folder:** `/data/patient/2152-03-20_18-43-52_s50184397/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2152-03-20_18-43-52_s50184397/6631d848-2c0cb2c2-f85d6490-f5df355f-11011cb8.jpg`, `/data/patient/2152-03-20_18-43-52_s50184397/89d3e1e1-ba4a0822-50e768c0-bbb29675-c5d05684.jpg`, `/data/patient/2152-03-20_18-43-52_s50184397/bd537505-f8ac7ed0-ba0e15df-386c3f65-90c4f4f1.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** Known pneumocystis pneumonia.
 
 COMPARISONS:  ___.

**TECHNIQUE:** Chest, AP upright and lateral.

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