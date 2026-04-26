# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14213287`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56237499`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 57975962
- **Date:** 2162-07-25 03:02:25
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2162-07-25_03-02-25_s57975962/`
- **Report:** `/data/patient/2162-07-25_03-02-25_s57975962/report.txt`
- **Images:** `/data/patient/2162-07-25_03-02-25_s57975962/4774bd11-ee7361e1-bd887280-f3a06036-3e636b3e.jpg`, `/data/patient/2162-07-25_03-02-25_s57975962/b7bd32a8-4cf22df1-81612a8c-d36d71b4-2787c2b5.jpg`

## Target Study

- **Study ID:** 56237499
- **Date:** 2163-01-05 11:59:07
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2163-01-05_11-59-07_s56237499/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2163-01-05_11-59-07_s56237499/db368d36-8c00c286-fd73c287-46b788dc-3238c890.jpg`
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