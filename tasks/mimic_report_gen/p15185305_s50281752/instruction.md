# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15185305`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50281752`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58286219
- **Date:** 2160-05-19 05:01:54
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2160-05-19_05-01-54_s58286219/`
- **Report:** `/data/patient/2160-05-19_05-01-54_s58286219/report.txt`
- **Images:** `/data/patient/2160-05-19_05-01-54_s58286219/27a246f8-b5019c81-a24b85d4-f3befa95-680ee871.jpg`, `/data/patient/2160-05-19_05-01-54_s58286219/7c2b70be-625cb0d4-aaf7b0f6-84685c72-50a04089.jpg`

### Prior Study 2: 50399800
- **Date:** 2160-05-20 05:34:59
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2160-05-20_05-34-59_s50399800/`
- **Report:** `/data/patient/2160-05-20_05-34-59_s50399800/report.txt`
- **Images:** `/data/patient/2160-05-20_05-34-59_s50399800/ddf73353-2bd13067-b8238f63-0ee1fa88-b917f360.jpg`

### Prior Study 3: 52381727
- **Date:** 2160-05-22 05:34:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2160-05-22_05-34-06_s52381727/`
- **Report:** `/data/patient/2160-05-22_05-34-06_s52381727/report.txt`
- **Images:** `/data/patient/2160-05-22_05-34-06_s52381727/2b387f17-5b587878-eab57bc7-959a3a13-68001f85.jpg`

### Prior Study 4: 58478940
- **Date:** 2160-05-23 06:04:36
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2160-05-23_06-04-36_s58478940/`
- **Report:** `/data/patient/2160-05-23_06-04-36_s58478940/report.txt`
- **Images:** `/data/patient/2160-05-23_06-04-36_s58478940/dbdd8fb8-dce8cc76-b74aa4de-722deb19-bdcfe5ca.jpg`

## Target Study

- **Study ID:** 50281752
- **Date:** 2160-05-25 10:31:41
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2160-05-25_10-31-41_s50281752/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2160-05-25_10-31-41_s50281752/97766a6d-6ee96b98-90cacba0-3eb50d93-77416ad1.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Increased work of breath after eating.  Evaluate for aspiration.
 
 COMPARISONS:  Chest radiograph ___. Chest  radiograph ___.

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