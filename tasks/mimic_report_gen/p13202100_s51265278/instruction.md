# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13202100`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51265278`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 50109176
- **Date:** 2138-10-31 23:41:18
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, AP, LATERAL
- **Folder:** `/data/patient/2138-10-31_23-41-18_s50109176/`
- **Report:** `/data/patient/2138-10-31_23-41-18_s50109176/report.txt`
- **Images:** `/data/patient/2138-10-31_23-41-18_s50109176/4f83231e-ae6e7b91-bf1ea6b3-6053e3f6-55fc3e1f.jpg`, `/data/patient/2138-10-31_23-41-18_s50109176/52e4bfec-0c5b972b-cbcd589e-3cd83f95-12d14023.jpg`, `/data/patient/2138-10-31_23-41-18_s50109176/89b0ebca-d32862e8-5268f3d8-5b946fe8-a2876759.jpg`, `/data/patient/2138-10-31_23-41-18_s50109176/cb5f3772-130f7aca-79e132d0-9724feeb-6f07f744.jpg`

## Target Study

- **Study ID:** 51265278
- **Date:** 2138-11-17 16:28:37
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2138-11-17_16-28-37_s51265278/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2138-11-17_16-28-37_s51265278/0d5def63-8ca29ddc-bf6bde42-fab8887f-19a6e96c.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**TECHNIQUE:** Chest, portable AP view.

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