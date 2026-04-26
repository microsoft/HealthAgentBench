# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12340737`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51192088`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58757200
- **Date:** 2193-03-22 07:58:38
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2193-03-22_07-58-38_s58757200/`
- **Report:** `/data/patient/2193-03-22_07-58-38_s58757200/report.txt`
- **Images:** `/data/patient/2193-03-22_07-58-38_s58757200/6eb24aca-5687f160-c7d0c498-3d8a1abf-05bf0b8c.jpg`

## Target Study

- **Study ID:** 51192088
- **Date:** 2193-04-26 12:13:46
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2193-04-26_12-13-46_s51192088/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2193-04-26_12-13-46_s51192088/eae9b998-2b29a12b-6d6fd4c2-8227ce7b-7f1c4262.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** A-fib, assess for acute cardiopulmonary abnormality

**TECHNIQUE:** Portable supine chest radiograph

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