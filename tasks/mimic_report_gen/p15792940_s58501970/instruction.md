# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15792940`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `58501970`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52559222
- **Date:** 2162-02-08 19:26:47
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2162-02-08_19-26-47_s52559222/`
- **Report:** `/data/patient/2162-02-08_19-26-47_s52559222/report.txt`
- **Images:** `/data/patient/2162-02-08_19-26-47_s52559222/e1b1e9b3-4c57d726-b37866dd-872d5448-027a7484.jpg`

## Target Study

- **Study ID:** 58501970
- **Date:** 2162-02-11 13:02:23
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2162-02-11_13-02-23_s58501970/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2162-02-11_13-02-23_s58501970/6a53a787-2e1025f2-59359f42-140f8938-45899305.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** ___-year-old male with recent pneumonia in need of interval
 assessment.
 
 STUDY:  Portable AP upright chest radiograph.

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