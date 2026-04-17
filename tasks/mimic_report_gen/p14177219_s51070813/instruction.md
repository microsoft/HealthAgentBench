# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14177219`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51070813`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 55111273
- **Date:** 2190-08-31 20:50:43
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2190-08-31_20-50-43_s55111273/`
- **Report:** `/data/patient/2190-08-31_20-50-43_s55111273/report.txt`
- **Images:** `/data/patient/2190-08-31_20-50-43_s55111273/0e44e612-dc278112-36de945c-ddc24b3d-392ee655.jpg`, `/data/patient/2190-08-31_20-50-43_s55111273/a8175445-d55b2d93-a5a3a22c-7662cb0a-6519b608.jpg`

### Prior Study 2: 57001920
- **Date:** 2190-11-15 15:21:27
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2190-11-15_15-21-27_s57001920/`
- **Report:** `/data/patient/2190-11-15_15-21-27_s57001920/report.txt`
- **Images:** `/data/patient/2190-11-15_15-21-27_s57001920/0e7807f6-04937b8e-ac237c79-1200da23-76b0b8e3.jpg`, `/data/patient/2190-11-15_15-21-27_s57001920/a11f2215-35bfbcfd-ab112ef2-f4a24f09-a770ee61.jpg`

### Prior Study 3: 52589781
- **Date:** 2191-01-22 08:46:36
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL, PA
- **Folder:** `/data/patient/2191-01-22_08-46-36_s52589781/`
- **Report:** `/data/patient/2191-01-22_08-46-36_s52589781/report.txt`
- **Images:** `/data/patient/2191-01-22_08-46-36_s52589781/027b4660-9fc20c6a-35de711b-876f0690-f2fcb5a3.jpg`, `/data/patient/2191-01-22_08-46-36_s52589781/11f9c16d-c60a6b46-3ec2ba36-c76fcdca-0d9f54b0.jpg`, `/data/patient/2191-01-22_08-46-36_s52589781/2583e77d-666ff867-9384b210-c059e9e6-31c7da01.jpg`

### Prior Study 4: 57812270
- **Date:** 2191-11-22 03:26:55
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2191-11-22_03-26-55_s57812270/`
- **Report:** `/data/patient/2191-11-22_03-26-55_s57812270/report.txt`
- **Images:** `/data/patient/2191-11-22_03-26-55_s57812270/efff7e71-8fb08183-a867eeaa-1bf8c237-82103b3e.jpg`

## Target Study

- **Study ID:** 51070813
- **Date:** 2193-02-18 09:48:16
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2193-02-18_09-48-16_s51070813/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2193-02-18_09-48-16_s51070813/3066a927-be47610c-a0348792-a8178259-d9cc2fa5.jpg`, `/data/patient/2193-02-18_09-48-16_s51070813/8aeadf93-9670a6fd-2e65b3ce-0719a2c7-d178e34c.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___ year old man with immunosuppression, hx chf, cough 4 weeks  //
 r/o pna

**TECHNIQUE:** Chest PA and lateral

**COMPARISON:** Preop chest radiograph dated ___ and portable chest
 radiograph dated ___

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