# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13120957`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `57697281`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 55681597
- **Date:** 2163-05-26 08:06:04
- **Procedure:** 
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2163-05-26_08-06-04_s55681597/`
- **Report:** `/data/patient/2163-05-26_08-06-04_s55681597/report.txt`
- **Images:** `/data/patient/2163-05-26_08-06-04_s55681597/98fa0073-4a72a84a-07d17d1b-80f5bc40-e729e67e.jpg`, `/data/patient/2163-05-26_08-06-04_s55681597/d53ea806-f9b5f637-2a0ee3e9-a8409e3d-56e8cf0f.jpg`

## Target Study

- **Study ID:** 57697281
- **Date:** 2167-10-21 13:54:28
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2167-10-21_13-54-28_s57697281/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2167-10-21_13-54-28_s57697281/159f8b16-a8da78c3-2dab8f92-5577b199-2d544ffc.jpg`, `/data/patient/2167-10-21_13-54-28_s57697281/95133322-5ad8fb3e-dea16125-70e718db-6cef790a.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___M with patellar tendon rupture  // pre-op

**TECHNIQUE:** AP and lateral views of the chest.

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