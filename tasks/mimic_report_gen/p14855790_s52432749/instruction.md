# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14855790`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `52432749`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53038366
- **Date:** 2165-11-24 21:44:56
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2165-11-24_21-44-56_s53038366/`
- **Report:** `/data/patient/2165-11-24_21-44-56_s53038366/report.txt`
- **Images:** `/data/patient/2165-11-24_21-44-56_s53038366/5d3b28e1-1aac3fe6-a4122890-9105accb-061b8489.jpg`

### Prior Study 2: 53565184
- **Date:** 2168-12-15 12:57:33
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2168-12-15_12-57-33_s53565184/`
- **Report:** `/data/patient/2168-12-15_12-57-33_s53565184/report.txt`
- **Images:** `/data/patient/2168-12-15_12-57-33_s53565184/886b46d2-5577e6fc-fe1bb0e6-08228079-9b623407.jpg`

## Target Study

- **Study ID:** 52432749
- **Date:** 2168-12-16 14:27:17
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2168-12-16_14-27-17_s52432749/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2168-12-16_14-27-17_s52432749/4a166e66-b64873d3-ed07d3ae-fc22f26a-6c154a1a.jpg`, `/data/patient/2168-12-16_14-27-17_s52432749/b2187498-bd6044fd-89eafb88-63b96bdd-2794d412.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PA AND LAT)

**INDICATION:** ___-year-old man with HTN, HLD, CAD s/p PCI ___, DM2 presenting
 with chest pressure, also productive cough x 4 weeks; evaluate for focal
 consolidation to suggest PNA, airway disease?

**COMPARISON:** Chest radiograph dated ___.

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