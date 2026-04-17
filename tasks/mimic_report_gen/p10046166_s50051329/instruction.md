# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `10046166`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50051329`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 56173345
- **Date:** 2132-12-07 19:24:25
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2132-12-07_19-24-25_s56173345/`
- **Report:** `/data/patient/2132-12-07_19-24-25_s56173345/report.txt`
- **Images:** `/data/patient/2132-12-07_19-24-25_s56173345/da33ac9f-b047f007-dd9e0ac7-81b4a35e-bb2b6b5b.jpg`

### Prior Study 2: 57977208
- **Date:** 2132-12-08 12:48:50
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2132-12-08_12-48-50_s57977208/`
- **Report:** `/data/patient/2132-12-08_12-48-50_s57977208/report.txt`
- **Images:** `/data/patient/2132-12-08_12-48-50_s57977208/e2856783-ffa5ec26-043b0303-21aeddc6-b11b2876.jpg`

### Prior Study 3: 53492798
- **Date:** 2133-03-06 20:00:00
- **Procedure:** Performed Desc
- **Views:** PA, PA, LL
- **Folder:** `/data/patient/2133-03-06_20-00-00_s53492798/`
- **Report:** `/data/patient/2133-03-06_20-00-00_s53492798/report.txt`
- **Images:** `/data/patient/2133-03-06_20-00-00_s53492798/18f0fd6d-f513afc9-e4aa8de2-bc5ac0d6-ea3daaff.jpg`, `/data/patient/2133-03-06_20-00-00_s53492798/7d5ef12b-34d86e32-207566d6-d5ed6f02-cd868f2c.jpg`, `/data/patient/2133-03-06_20-00-00_s53492798/eab11c59-32a5b9b8-b8d335fa-ce06c5fa-5bde0499.jpg`

### Prior Study 4: 57379357
- **Date:** 2133-03-21 11:57:19
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2133-03-21_11-57-19_s57379357/`
- **Report:** `/data/patient/2133-03-21_11-57-19_s57379357/report.txt`
- **Images:** `/data/patient/2133-03-21_11-57-19_s57379357/6e511483-c7e1601c-76890b2f-b0c6b55d-e53bcbf6.jpg`, `/data/patient/2133-03-21_11-57-19_s57379357/e5ba5704-ce2f09d3-e28fe2a2-8a9aca96-86f4966a.jpg`

### Prior Study 5: 51738740
- **Date:** 2133-09-19 19:39:24
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, LATERAL
- **Folder:** `/data/patient/2133-09-19_19-39-24_s51738740/`
- **Report:** `/data/patient/2133-09-19_19-39-24_s51738740/report.txt`
- **Images:** `/data/patient/2133-09-19_19-39-24_s51738740/3a8a17fc-3cd357d9-83466363-91dc5a06-a401e5ed.jpg`, `/data/patient/2133-09-19_19-39-24_s51738740/6130440f-929f5fae-e4b47406-634aedcb-3dd112ec.jpg`, `/data/patient/2133-09-19_19-39-24_s51738740/6fde5b65-a0efc54f-dbd690f2-5f9f941a-2b770631.jpg`

## Target Study

- **Study ID:** 50051329
- **Date:** 2133-10-06 00:42:28
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2133-10-06_00-42-28_s50051329/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2133-10-06_00-42-28_s50051329/427446c1-881f5cce-85191ce1-91a58ba9-0a57d3f5.jpg`, `/data/patient/2133-10-06_00-42-28_s50051329/abea5eb9-b7c32823-3a14c5ca-77868030-69c83139.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old male with history of metastatic melanoma, presenting
 with confusion and somnolence.  Evaluate for acute cardiopulmonary process.

**TECHNIQUE:** AP upright and lateral chest radiograph.

**COMPARISON:** ___.

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