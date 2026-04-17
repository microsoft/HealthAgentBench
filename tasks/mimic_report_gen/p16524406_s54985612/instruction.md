# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `16524406`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54985612`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54562273
- **Date:** 2190-01-31 22:05:35
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2190-01-31_22-05-35_s54562273/`
- **Report:** `/data/patient/2190-01-31_22-05-35_s54562273/report.txt`
- **Images:** `/data/patient/2190-01-31_22-05-35_s54562273/db019b7e-d9ed7caa-dce2242f-4d94ffd2-276acfb6.jpg`, `/data/patient/2190-01-31_22-05-35_s54562273/e7c6ee1e-e78f4a5f-8d06b880-0facc167-9037ed6a.jpg`

### Prior Study 2: 56536310
- **Date:** 2190-02-08 15:32:10
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2190-02-08_15-32-10_s56536310/`
- **Report:** `/data/patient/2190-02-08_15-32-10_s56536310/report.txt`
- **Images:** `/data/patient/2190-02-08_15-32-10_s56536310/924ee1f2-b4628f80-13244a4a-e74a358f-825abf61.jpg`

## Target Study

- **Study ID:** 54985612
- **Date:** 2194-01-16 19:48:37
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2194-01-16_19-48-37_s54985612/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2194-01-16_19-48-37_s54985612/cae34b8f-cef454bf-250bd88e-8bef265d-9a3f0172.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PORTABLE AP)

**INDICATION:** History: ___F with post intubation

**TECHNIQUE:** Portable upright AP view of the chest

**COMPARISON:** Chest radiograph ___

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