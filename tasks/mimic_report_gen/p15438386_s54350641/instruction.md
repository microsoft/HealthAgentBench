# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15438386`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54350641`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59022925
- **Date:** 2161-08-26 12:58:20
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2161-08-26_12-58-20_s59022925/`
- **Report:** `/data/patient/2161-08-26_12-58-20_s59022925/report.txt`
- **Images:** `/data/patient/2161-08-26_12-58-20_s59022925/57f7f75e-91517fb3-4071303d-6f325ed5-5daca800.jpg`, `/data/patient/2161-08-26_12-58-20_s59022925/d51e424a-a44ba612-1f92bcc5-32008577-36bdedd0.jpg`

### Prior Study 2: 50994417
- **Date:** 2162-08-01 11:41:41
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2162-08-01_11-41-41_s50994417/`
- **Report:** `/data/patient/2162-08-01_11-41-41_s50994417/report.txt`
- **Images:** `/data/patient/2162-08-01_11-41-41_s50994417/081b6db8-da3b5047-573fbc16-9aa955fa-d35d3cc2.jpg`, `/data/patient/2162-08-01_11-41-41_s50994417/88452747-3f314c21-22193cd6-21965317-a568535d.jpg`, `/data/patient/2162-08-01_11-41-41_s50994417/dd7b0ab6-fd3ea03d-b2a70c10-5eca94a7-a74d42be.jpg`

### Prior Study 3: 59891992
- **Date:** 2162-09-01 10:26:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2162-09-01_10-26-46_s59891992/`
- **Report:** `/data/patient/2162-09-01_10-26-46_s59891992/report.txt`
- **Images:** `/data/patient/2162-09-01_10-26-46_s59891992/97e98c24-079ba543-3cfe0fbe-b97b30b8-bbd0e9a5.jpg`, `/data/patient/2162-09-01_10-26-46_s59891992/b6efc4df-c96de5ed-5551d21b-f99936ca-082ca79e.jpg`

### Prior Study 4: 55060674
- **Date:** 2162-09-20 19:22:05
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2162-09-20_19-22-05_s55060674/`
- **Report:** `/data/patient/2162-09-20_19-22-05_s55060674/report.txt`
- **Images:** `/data/patient/2162-09-20_19-22-05_s55060674/5f7fabe4-ef89e705-401654db-7da95115-a824cf01.jpg`

## Target Study

- **Study ID:** 54350641
- **Date:** 2162-09-20 05:45:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2162-09-20_05-45-06_s54350641/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2162-09-20_05-45-06_s54350641/76e72399-4ee134f7-c1d4538e-8c0a7451-bacc3a48.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Small-bowel obstruction, status post nasogastric tube placement. 
 Evaluate tube position.

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