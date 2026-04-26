# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `16116557`
- 1 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56362705`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 51951386
- **Date:** 2152-06-03 09:22:39
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, PA, LATERAL
- **Folder:** `/data/patient/2152-06-03_09-22-39_s51951386/`
- **Report:** `/data/patient/2152-06-03_09-22-39_s51951386/report.txt`
- **Images:** `/data/patient/2152-06-03_09-22-39_s51951386/06aeac02-b53537f5-fc5cd426-d1528a0c-0b563e39.jpg`, `/data/patient/2152-06-03_09-22-39_s51951386/0bb60711-8098a084-5f12d2bb-e8739a70-870e72a1.jpg`, `/data/patient/2152-06-03_09-22-39_s51951386/eac51eb0-1de39331-93d4cd9e-2ea34983-47a728bc.jpg`

## Target Study

- **Study ID:** 56362705
- **Date:** 2152-12-29 01:27:42
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, PA
- **Folder:** `/data/patient/2152-12-29_01-27-42_s56362705/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2152-12-29_01-27-42_s56362705/1a648bc5-393857b7-f4dcfea5-cc7f74af-b8d8d2fe.jpg`, `/data/patient/2152-12-29_01-27-42_s56362705/4983ed0a-abcbaeb0-442211c9-9b2054ad-8fdf0f80.jpg`, `/data/patient/2152-12-29_01-27-42_s56362705/64613c7b-ce9fb911-c2eb42ab-41a905ea-97ce9a9d.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old with HIV and fever.

**TECHNIQUE:** Frontal and lateral radiographs of the chest were obtained.

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