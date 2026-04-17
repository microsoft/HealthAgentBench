# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14504940`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `58521372`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 55011437
- **Date:** 2192-10-02 12:24:42
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2192-10-02_12-24-42_s55011437/`
- **Report:** `/data/patient/2192-10-02_12-24-42_s55011437/report.txt`
- **Images:** `/data/patient/2192-10-02_12-24-42_s55011437/7c41a809-f93b8fdb-32b0f64f-3c464002-d1751a7c.jpg`, `/data/patient/2192-10-02_12-24-42_s55011437/93df2443-2b80a0f4-6c12dc92-910966a7-3da34ae3.jpg`

## Target Study

- **Study ID:** 58521372
- **Date:** 2193-10-17 16:35:15
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, PA, LATERAL
- **Folder:** `/data/patient/2193-10-17_16-35-15_s58521372/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2193-10-17_16-35-15_s58521372/1675afce-31756f63-a165a417-94a2c4ab-41fa955f.jpg`, `/data/patient/2193-10-17_16-35-15_s58521372/4e5ddaa7-63711567-067f2a36-70ca8cbf-3684164e.jpg`, `/data/patient/2193-10-17_16-35-15_s58521372/ba93c845-aff601a7-a7342bac-ad387748-7af110b6.jpg`

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