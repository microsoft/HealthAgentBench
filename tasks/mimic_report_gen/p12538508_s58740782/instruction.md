# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12538508`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `58740782`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 51621137
- **Date:** 2161-04-02 20:40:13
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2161-04-02_20-40-13_s51621137/`
- **Report:** `/data/patient/2161-04-02_20-40-13_s51621137/report.txt`
- **Images:** `/data/patient/2161-04-02_20-40-13_s51621137/0beab5cd-dd1bb454-0df993cf-f3c0ae3d-8f0e0c27.jpg`

### Prior Study 2: 55670303
- **Date:** 2161-04-04 13:15:19
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2161-04-04_13-15-19_s55670303/`
- **Report:** `/data/patient/2161-04-04_13-15-19_s55670303/report.txt`
- **Images:** `/data/patient/2161-04-04_13-15-19_s55670303/4639cd47-e73a89d3-48315552-a87979a8-7dd4f191.jpg`

## Target Study

- **Study ID:** 58740782
- **Date:** 2161-11-26 08:56:50
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2161-11-26_08-56-50_s58740782/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2161-11-26_08-56-50_s58740782/d423cd88-d0739c64-5212e268-96f30c3b-7bd9f6ae.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old man with cough, dyspnea, question pneumonia.
 
 COMPARISONS:  Portable AP radiograph from ___.

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