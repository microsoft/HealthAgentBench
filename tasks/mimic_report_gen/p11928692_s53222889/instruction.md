# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `11928692`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `53222889`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54164323
- **Date:** 2172-07-31 01:24:45
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP, AP
- **Folder:** `/data/patient/2172-07-31_01-24-45_s54164323/`
- **Report:** `/data/patient/2172-07-31_01-24-45_s54164323/report.txt`
- **Images:** `/data/patient/2172-07-31_01-24-45_s54164323/129d1cfc-6a372c68-c84b5eaf-53903d40-670d6d9c.jpg`, `/data/patient/2172-07-31_01-24-45_s54164323/3606dd6e-1d4e216a-0251de47-cb1445d6-fcb76ed3.jpg`, `/data/patient/2172-07-31_01-24-45_s54164323/405e6cc1-70b9d9b3-1c752677-010c4ee9-b217b783.jpg`, `/data/patient/2172-07-31_01-24-45_s54164323/5475bdcc-37f6b853-142a043b-3e6572f9-5b71d475.jpg`

### Prior Study 2: 55947318
- **Date:** 2173-02-27 18:49:39
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2173-02-27_18-49-39_s55947318/`
- **Report:** `/data/patient/2173-02-27_18-49-39_s55947318/report.txt`
- **Images:** `/data/patient/2173-02-27_18-49-39_s55947318/2c5c8a39-6ae3dd9e-2b4d5279-6bb07505-1b57f5ab.jpg`, `/data/patient/2173-02-27_18-49-39_s55947318/df66e950-78bfa09d-ccc14e43-193ef713-3c2bd5a4.jpg`

## Target Study

- **Study ID:** 53222889
- **Date:** 2175-03-02 13:35:56
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP, AP
- **Folder:** `/data/patient/2175-03-02_13-35-56_s53222889/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2175-03-02_13-35-56_s53222889/21d9c2b2-5e94a363-aa3b9d61-a6858503-795b84ab.jpg`, `/data/patient/2175-03-02_13-35-56_s53222889/2ea8f7b3-8e1fd4ff-87a29ebc-702190c4-45123977.jpg`, `/data/patient/2175-03-02_13-35-56_s53222889/6bd4c046-822ab57b-56c2ade0-5990ad2d-449af809.jpg`, `/data/patient/2175-03-02_13-35-56_s53222889/d1b9813f-08d920a6-85c9bb6f-c516c1ee-a56f9d38.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___ year old woman with persistent cough and bilateral crackles 
 // rule out pneumonia

**TECHNIQUE:** Chest PA and lateral

**COMPARISON:** Prior radiographs the chest dated ___ to ___.

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