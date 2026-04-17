# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `11540283`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50535882`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 51230608
- **Date:** 2191-09-20 08:56:07
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2191-09-20_08-56-07_s51230608/`
- **Report:** `/data/patient/2191-09-20_08-56-07_s51230608/report.txt`
- **Images:** `/data/patient/2191-09-20_08-56-07_s51230608/21f4d559-0dfff001-b12a1cc5-64419048-1301fa93.jpg`, `/data/patient/2191-09-20_08-56-07_s51230608/e68bb7df-05039df8-44346b6b-c34ca52e-a92432c7.jpg`

### Prior Study 2: 51114398
- **Date:** 2193-11-30 20:43:17
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2193-11-30_20-43-17_s51114398/`
- **Report:** `/data/patient/2193-11-30_20-43-17_s51114398/report.txt`
- **Images:** `/data/patient/2193-11-30_20-43-17_s51114398/ff4180bc-fa800289-1e6a39c6-4c38b356-ad513e6a.jpg`

### Prior Study 3: 56385625
- **Date:** 2193-12-01 03:53:51
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2193-12-01_03-53-51_s56385625/`
- **Report:** `/data/patient/2193-12-01_03-53-51_s56385625/report.txt`
- **Images:** `/data/patient/2193-12-01_03-53-51_s56385625/17d85861-7a43410c-8f9b5b54-4629da0d-5647276d.jpg`

### Prior Study 4: 58773579
- **Date:** 2195-02-23 17:05:10
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2195-02-23_17-05-10_s58773579/`
- **Report:** `/data/patient/2195-02-23_17-05-10_s58773579/report.txt`
- **Images:** `/data/patient/2195-02-23_17-05-10_s58773579/456d62e4-2e673ffe-83ccc42f-f942c7fb-d5dbc58b.jpg`, `/data/patient/2195-02-23_17-05-10_s58773579/4a6b6a7c-83ed2cdc-41c74d6e-ed8815a2-84ed02ff.jpg`

## Target Study

- **Study ID:** 50535882
- **Date:** 2195-12-25 16:07:26
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2195-12-25_16-07-26_s50535882/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2195-12-25_16-07-26_s50535882/039986b2-a4be9c1e-48fe40eb-46b7fccd-c779bad9.jpg`, `/data/patient/2195-12-25_16-07-26_s50535882/dd4903ae-cb2e72fa-55472aa9-b4e1aa63-9c138d54.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** Chest radiograph

**INDICATION:** ___ year old man with chronic cough x 3 mo. no fever or sob  //
 r/o pna

**TECHNIQUE:** Chest PA and lateral

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