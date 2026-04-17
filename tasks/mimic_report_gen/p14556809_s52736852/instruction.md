# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14556809`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `52736852`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52810254
- **Date:** 2199-06-30 14:24:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2199-06-30_14-24-46_s52810254/`
- **Report:** `/data/patient/2199-06-30_14-24-46_s52810254/report.txt`
- **Images:** `/data/patient/2199-06-30_14-24-46_s52810254/3555a31b-7de6859b-3d2e1279-2c0be9b8-f1030977.jpg`, `/data/patient/2199-06-30_14-24-46_s52810254/4ad53a55-132d3197-10100b09-48d1f2ba-43059e75.jpg`

### Prior Study 2: 53292802
- **Date:** 2199-07-26 15:22:39
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, PA
- **Folder:** `/data/patient/2199-07-26_15-22-39_s53292802/`
- **Report:** `/data/patient/2199-07-26_15-22-39_s53292802/report.txt`
- **Images:** `/data/patient/2199-07-26_15-22-39_s53292802/31fd8c2d-92304fd6-93dd126a-3ed4e346-c485de34.jpg`, `/data/patient/2199-07-26_15-22-39_s53292802/5c6bee5b-5201ac36-cf58d846-9697b015-29bf9fb3.jpg`, `/data/patient/2199-07-26_15-22-39_s53292802/f853039e-e541ff3f-875071bd-62705831-03bd8d9e.jpg`

### Prior Study 3: 52110747
- **Date:** 2200-04-18 09:57:42
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2200-04-18_09-57-42_s52110747/`
- **Report:** `/data/patient/2200-04-18_09-57-42_s52110747/report.txt`
- **Images:** `/data/patient/2200-04-18_09-57-42_s52110747/2c2536da-bc7670f1-2bbb98a2-e03017cc-87c616ee.jpg`

### Prior Study 4: 52436795
- **Date:** 2200-04-20 12:33:05
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , LL
- **Folder:** `/data/patient/2200-04-20_12-33-05_s52436795/`
- **Report:** `/data/patient/2200-04-20_12-33-05_s52436795/report.txt`
- **Images:** `/data/patient/2200-04-20_12-33-05_s52436795/37130de3-468e154c-e1a6e62c-86eb636b-7b038a9a.jpg`, `/data/patient/2200-04-20_12-33-05_s52436795/90358b98-c82518b0-b607a82f-38c80761-0ca422aa.jpg`

### Prior Study 5: 50432000
- **Date:** 2202-06-22 14:07:00
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2202-06-22_14-07-00_s50432000/`
- **Report:** `/data/patient/2202-06-22_14-07-00_s50432000/report.txt`
- **Images:** `/data/patient/2202-06-22_14-07-00_s50432000/7a75be73-77ed1349-e974ef60-e017dcfa-5be7d3fa.jpg`, `/data/patient/2202-06-22_14-07-00_s50432000/df15edc0-6b4fce10-50e4beb8-40b31531-05dc3b49.jpg`

### Prior Study 6: 53779297
- **Date:** 2203-04-12 16:14:22
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2203-04-12_16-14-22_s53779297/`
- **Report:** `/data/patient/2203-04-12_16-14-22_s53779297/report.txt`
- **Images:** `/data/patient/2203-04-12_16-14-22_s53779297/ba22c676-fe74f3b9-b6e53609-c7281450-9f52ce69.jpg`, `/data/patient/2203-04-12_16-14-22_s53779297/e965dfde-aaa9927d-fd329e7e-4a8af64b-ed32a2d7.jpg`

## Target Study

- **Study ID:** 52736852
- **Date:** 2204-05-19 10:58:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2204-05-19_10-58-18_s52736852/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2204-05-19_10-58-18_s52736852/2dfbf7e0-85ed2f34-4c60e220-a5f1fa98-464b3ce2.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___ year old woman with desaturation on RA to 70s  // ?pneumonia

**TECHNIQUE:** Chest PA and lateral

**COMPARISON:** Chest radiograph from ___ and CT from ___

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