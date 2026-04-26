# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12145137`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54833205`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54100996
- **Date:** 2122-07-30 17:49:49
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2122-07-30_17-49-49_s54100996/`
- **Report:** `/data/patient/2122-07-30_17-49-49_s54100996/report.txt`
- **Images:** `/data/patient/2122-07-30_17-49-49_s54100996/070b58a0-da9b8080-6eeeaf5a-46226e7b-2f9453fa.jpg`, `/data/patient/2122-07-30_17-49-49_s54100996/c875e4c8-ab736220-04569ba0-857889ce-042ea536.jpg`

## Target Study

- **Study ID:** 54833205
- **Date:** 2122-11-19 01:51:05
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2122-11-19_01-51-05_s54833205/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2122-11-19_01-51-05_s54833205/61b4d5e0-66a2bcaf-6c4d6c19-6b735e59-b1390cb2.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Evaluation of patient with abdominal pain and lactic acidosis.

**COMPARISON:** Chest CT from ___ and chest radiograph from
 ___.

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