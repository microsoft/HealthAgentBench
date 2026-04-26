# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12966004`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55553875`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 57399078
- **Date:** 2121-09-13 10:23:59
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2121-09-13_10-23-59_s57399078/`
- **Report:** `/data/patient/2121-09-13_10-23-59_s57399078/report.txt`
- **Images:** `/data/patient/2121-09-13_10-23-59_s57399078/85904052-28d3a26a-9a756f5e-03c7a51b-3a9f5f19.jpg`

### Prior Study 2: 59842808
- **Date:** 2121-09-13 19:23:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2121-09-13_19-23-03_s59842808/`
- **Report:** `/data/patient/2121-09-13_19-23-03_s59842808/report.txt`
- **Images:** `/data/patient/2121-09-13_19-23-03_s59842808/bbdcb05c-156dd562-ae7470ee-946facfc-07efcfcd.jpg`

## Target Study

- **Study ID:** 55553875
- **Date:** 2121-09-15 07:54:40
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2121-09-15_07-54-40_s55553875/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2121-09-15_07-54-40_s55553875/d506da5a-b2dad80c-f31e282e-15154de3-b4385bea.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** PE, status post PEA arrest, hypothermia protocol.  Assess for
 edema or infection.

**TECHNIQUE:** AP upright portable radiograph of the chest.

**COMPARISON:** Chest radiograph from ___.

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