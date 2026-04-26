# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15541869`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50553646`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 55364313
- **Date:** 2148-02-25 18:40:50
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2148-02-25_18-40-50_s55364313/`
- **Report:** `/data/patient/2148-02-25_18-40-50_s55364313/report.txt`
- **Images:** `/data/patient/2148-02-25_18-40-50_s55364313/a5b415f2-b092fbdd-488fd0f8-0d4c383a-eed231bc.jpg`

### Prior Study 2: 55266015
- **Date:** 2148-03-02 14:38:29
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2148-03-02_14-38-29_s55266015/`
- **Report:** `/data/patient/2148-03-02_14-38-29_s55266015/report.txt`
- **Images:** `/data/patient/2148-03-02_14-38-29_s55266015/176e0588-2fc59c9a-096765cc-a04685eb-e860762a.jpg`, `/data/patient/2148-03-02_14-38-29_s55266015/a2958de9-3f5b2b3e-0f868adb-1bfb09df-e2f90c3e.jpg`

## Target Study

- **Study ID:** 50553646
- **Date:** 2148-03-23 13:37:00
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2148-03-23_13-37-00_s50553646/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2148-03-23_13-37-00_s50553646/7cd49c7e-4de451f1-91d968ae-81143d7e-0b2dd70f.jpg`, `/data/patient/2148-03-23_13-37-00_s50553646/912e2ddc-d5d8cb35-d2736bcd-4a25d08f-ee68cba1.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**COMPARISON:** CTA chest from ___ as well as a chest radiograph from
 ___.
 
 CLINICAL HISTORY:  Sepsis unknown source, abdominal pain and altered mental
 status.

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