# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17257913`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `57420525`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52072042
- **Date:** 2152-07-08 13:30:21
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2152-07-08_13-30-21_s52072042/`
- **Report:** `/data/patient/2152-07-08_13-30-21_s52072042/report.txt`
- **Images:** `/data/patient/2152-07-08_13-30-21_s52072042/a6aacacb-72188cab-113e38f7-dc63b7cb-e0b3cd1a.jpg`, `/data/patient/2152-07-08_13-30-21_s52072042/e872e235-dee5ac10-dfd4a5e4-e40a9a02-73e5ee8a.jpg`

## Target Study

- **Study ID:** 57420525
- **Date:** 2153-07-05 12:21:59
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2153-07-05_12-21-59_s57420525/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2153-07-05_12-21-59_s57420525/614cf968-41dc136f-73eb6d42-6b73032b-e0dde637.jpg`, `/data/patient/2153-07-05_12-21-59_s57420525/96970f3a-0571b454-3baba4d3-45236f65-abf7a9c6.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old male patient with cough, assess for abnormality.

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