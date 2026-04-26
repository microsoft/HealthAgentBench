# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14434800`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54259878`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52682048
- **Date:** 2131-06-14 11:50:41
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2131-06-14_11-50-41_s52682048/`
- **Report:** `/data/patient/2131-06-14_11-50-41_s52682048/report.txt`
- **Images:** `/data/patient/2131-06-14_11-50-41_s52682048/0d9ee316-000a9e0c-be78c74d-62923605-0315f8e4.jpg`

## Target Study

- **Study ID:** 54259878
- **Date:** 2131-11-14 16:19:54
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2131-11-14_16-19-54_s54259878/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2131-11-14_16-19-54_s54259878/2ff8144f-c833baaa-899af187-89dbc6ce-3adfc088.jpg`, `/data/patient/2131-11-14_16-19-54_s54259878/b25f2936-0120858b-2a77fcb0-43a6260d-c05b2818.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** Chest tightness.
 
 COMPARISONS:  ___.

**TECHNIQUE:** Chest, PA and lateral.

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