# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12369221`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50178679`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59986698
- **Date:** 2172-02-11 13:31:37
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP
- **Folder:** `/data/patient/2172-02-11_13-31-37_s59986698/`
- **Report:** `/data/patient/2172-02-11_13-31-37_s59986698/report.txt`
- **Images:** `/data/patient/2172-02-11_13-31-37_s59986698/417d5c5e-b521f965-35306684-68e7deb2-cda06f5c.jpg`

## Target Study

- **Study ID:** 50178679
- **Date:** 2172-05-22 18:04:28
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2172-05-22_18-04-28_s50178679/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2172-05-22_18-04-28_s50178679/3821a16d-3dd0338c-8485c8e1-c3cfcd50-05762b8b.jpg`, `/data/patient/2172-05-22_18-04-28_s50178679/861f9946-68cebd2f-e11dbfba-aaad1909-7ccc759e.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** ___-year-old female with fever and cough, change in mental status.

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