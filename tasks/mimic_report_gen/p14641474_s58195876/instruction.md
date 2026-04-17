# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14641474`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `58195876`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58836797
- **Date:** 2186-10-11 02:24:08
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2186-10-11_02-24-08_s58836797/`
- **Report:** `/data/patient/2186-10-11_02-24-08_s58836797/report.txt`
- **Images:** `/data/patient/2186-10-11_02-24-08_s58836797/29fa67ed-eafe7bd7-b310f744-078a1939-72c2aacb.jpg`

### Prior Study 2: 56168637
- **Date:** 2186-10-12 07:51:05
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2186-10-12_07-51-05_s56168637/`
- **Report:** `/data/patient/2186-10-12_07-51-05_s56168637/report.txt`
- **Images:** `/data/patient/2186-10-12_07-51-05_s56168637/fd15e7bf-1621a059-9416c9b7-f74f9113-61918f0f.jpg`

## Target Study

- **Study ID:** 58195876
- **Date:** 2189-10-27 14:29:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2189-10-27_14-29-46_s58195876/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2189-10-27_14-29-46_s58195876/4a819d4e-b5dd0e9c-b31a1805-8e048ace-b2c45a7c.jpg`, `/data/patient/2189-10-27_14-29-46_s58195876/a431832f-c2debb14-58876089-dc9b0d60-95e4c67f.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___F with history of chest pain, intermitting in nature as well
 left groin describes as pop and sharp sensation similar pain last week but
 resolved now states history of abdominal hernia (unable to feel on exam

**TECHNIQUE:** Chest PA and lateral

**COMPARISON:** Radiograph dated ___.

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