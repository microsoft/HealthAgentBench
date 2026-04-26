# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `11016935`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51683155`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54381763
- **Date:** 2158-01-24 22:36:30
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2158-01-24_22-36-30_s54381763/`
- **Report:** `/data/patient/2158-01-24_22-36-30_s54381763/report.txt`
- **Images:** `/data/patient/2158-01-24_22-36-30_s54381763/d7455c33-4a0f90a6-565ee283-906f14b4-c737ba31.jpg`, `/data/patient/2158-01-24_22-36-30_s54381763/ffe111af-f37e2ddf-0a7424d4-4b1cd736-be3f6e66.jpg`

## Target Study

- **Study ID:** 51683155
- **Date:** 2162-04-08 13:38:53
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2162-04-08_13-38-53_s51683155/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2162-04-08_13-38-53_s51683155/62fefce3-f6ecb665-461a4358-37a5af91-dec27897.jpg`, `/data/patient/2162-04-08_13-38-53_s51683155/7e26f6a7-ec126822-1bcdc587-a3f5d439-b4715eae.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PA AND LAT)

**INDICATION:** ___ year old man with chest pain. // Please evaluate for thoracic
 pathology.

**COMPARISON:** Chest radiograph dated ___
 CT chest without contrast ___

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