# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15094735`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `57678258`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 55874928
- **Date:** 2162-01-11 23:17:09
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2162-01-11_23-17-09_s55874928/`
- **Report:** `/data/patient/2162-01-11_23-17-09_s55874928/report.txt`
- **Images:** `/data/patient/2162-01-11_23-17-09_s55874928/fae734b5-cdbcad8f-13e2fcaf-8e2731ff-ca43dfa9.jpg`

## Target Study

- **Study ID:** 57678258
- **Date:** 2162-01-13 07:34:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2162-01-13_07-34-18_s57678258/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2162-01-13_07-34-18_s57678258/cff0405e-7c684aeb-122051b9-dec202c9-1dfbb41e.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Status post CABG with dyspnea.  Evaluate for edema.
 
 COMPARISONS:  Chest radiograph, ___.  Chest radiograph, ___.

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