# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `16043240`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51640383`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53861171
- **Date:** 2158-01-11 11:02:41
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2158-01-11_11-02-41_s53861171/`
- **Report:** `/data/patient/2158-01-11_11-02-41_s53861171/report.txt`
- **Images:** `/data/patient/2158-01-11_11-02-41_s53861171/a0c83599-da2ea7b7-03944f49-45a6b253-31fa3b34.jpg`

### Prior Study 2: 50307780
- **Date:** 2158-01-11 17:18:37
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2158-01-11_17-18-37_s50307780/`
- **Report:** `/data/patient/2158-01-11_17-18-37_s50307780/report.txt`
- **Images:** `/data/patient/2158-01-11_17-18-37_s50307780/05422169-24d04e58-5084d62b-7d1d9ce1-16bfe2af.jpg`

### Prior Study 3: 55694501
- **Date:** 2158-01-14 09:12:36
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2158-01-14_09-12-36_s55694501/`
- **Report:** `/data/patient/2158-01-14_09-12-36_s55694501/report.txt`
- **Images:** `/data/patient/2158-01-14_09-12-36_s55694501/8b60991f-624bc875-aa844f68-060004c2-1fdd9628.jpg`, `/data/patient/2158-01-14_09-12-36_s55694501/9cb7472a-803c242b-a9526718-19d7b53c-e332df01.jpg`

### Prior Study 4: 59721249
- **Date:** 2158-03-04 17:19:23
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2158-03-04_17-19-23_s59721249/`
- **Report:** `/data/patient/2158-03-04_17-19-23_s59721249/report.txt`
- **Images:** `/data/patient/2158-03-04_17-19-23_s59721249/b4a8be85-cd2ddd78-71d33835-f50791b5-18321dcd.jpg`, `/data/patient/2158-03-04_17-19-23_s59721249/bffeb923-b2e49523-b66fa14c-e5d62eb0-93afffd1.jpg`

## Target Study

- **Study ID:** 51640383
- **Date:** 2158-08-12 15:13:02
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2158-08-12_15-13-02_s51640383/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2158-08-12_15-13-02_s51640383/46f5be5f-70e3e741-542f6fde-edbbdbfe-a4ed00d6.jpg`, `/data/patient/2158-08-12_15-13-02_s51640383/603ec26c-efd8dad7-d9c3a4d2-f402b7a8-8b3ac5e7.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old with chronic cough and bibasilar rales.

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