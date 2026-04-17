# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13755940`
- 3 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54060800`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58666319
- **Date:** 2188-10-21 12:53:44
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2188-10-21_12-53-44_s58666319/`
- **Report:** `/data/patient/2188-10-21_12-53-44_s58666319/report.txt`
- **Images:** `/data/patient/2188-10-21_12-53-44_s58666319/57b2666a-699fa6ab-57992ba2-54520a2e-7ee60ae6.jpg`

### Prior Study 2: 51099690
- **Date:** 2188-10-24 18:43:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2188-10-24_18-43-18_s51099690/`
- **Report:** `/data/patient/2188-10-24_18-43-18_s51099690/report.txt`
- **Images:** `/data/patient/2188-10-24_18-43-18_s51099690/e53aee72-582b01ea-a370ca39-62ce5b25-e0eed2b3.jpg`

### Prior Study 3: 59900684
- **Date:** 2188-10-27 12:24:24
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2188-10-27_12-24-24_s59900684/`
- **Report:** `/data/patient/2188-10-27_12-24-24_s59900684/report.txt`
- **Images:** `/data/patient/2188-10-27_12-24-24_s59900684/4fe3e961-a3a02576-db1e637e-60077803-2a154636.jpg`

## Target Study

- **Study ID:** 54060800
- **Date:** 2188-10-27 14:51:19
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2188-10-27_14-51-19_s54060800/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2188-10-27_14-51-19_s54060800/9678dc02-54a05e84-f5efffa5-bc62e0a2-83dac014.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** Single frontal chest radiograph.
 
 COMPARISONS:  ___ dating back to ___.

**INDICATION:** ___-year-old female with atrial fibrillation and with rapid
 ventricular response, status post transesophageal echocardiogram 4 hours
 prior, now mottled and diaphoretic.  Evaluate for pneumomediastinum.

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