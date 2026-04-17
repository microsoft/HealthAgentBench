# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14312560`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55983006`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52078894
- **Date:** 2126-04-02 20:54:28
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2126-04-02_20-54-28_s52078894/`
- **Report:** `/data/patient/2126-04-02_20-54-28_s52078894/report.txt`
- **Images:** `/data/patient/2126-04-02_20-54-28_s52078894/cfc2ef1b-a194024a-6147d0d3-6d42379a-575c395f.jpg`, `/data/patient/2126-04-02_20-54-28_s52078894/ef44cff6-c00bc7fa-7a405dea-28717c25-1b5e3ac6.jpg`

### Prior Study 2: 54145592
- **Date:** 2126-08-02 04:11:09
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2126-08-02_04-11-09_s54145592/`
- **Report:** `/data/patient/2126-08-02_04-11-09_s54145592/report.txt`
- **Images:** `/data/patient/2126-08-02_04-11-09_s54145592/2e02dd1a-6c84da2d-c2df5435-9ac1ab07-f7351caa.jpg`

### Prior Study 3: 59332489
- **Date:** 2126-08-04 11:16:37
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2126-08-04_11-16-37_s59332489/`
- **Report:** `/data/patient/2126-08-04_11-16-37_s59332489/report.txt`
- **Images:** `/data/patient/2126-08-04_11-16-37_s59332489/a81e30c1-ca178bc2-f8d08051-953a1ecc-dc75088f.jpg`, `/data/patient/2126-08-04_11-16-37_s59332489/ae39f4d0-b0da3b02-52929cd2-b6698aad-a681fd22.jpg`

### Prior Study 4: 57784780
- **Date:** 2127-06-28 12:09:18
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2127-06-28_12-09-18_s57784780/`
- **Report:** `/data/patient/2127-06-28_12-09-18_s57784780/report.txt`
- **Images:** `/data/patient/2127-06-28_12-09-18_s57784780/278ebde6-e46251bd-4f894b8e-3ea1ab66-cbea5d97.jpg`, `/data/patient/2127-06-28_12-09-18_s57784780/2ad8c1ee-2b9971e8-22aef719-feb89bce-e6c1aa69.jpg`

### Prior Study 5: 50617748
- **Date:** 2130-03-10 14:03:25
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2130-03-10_14-03-25_s50617748/`
- **Report:** `/data/patient/2130-03-10_14-03-25_s50617748/report.txt`
- **Images:** `/data/patient/2130-03-10_14-03-25_s50617748/513c2a6c-c081efd7-5d2b0a10-5ae31d2c-1664a879.jpg`

## Target Study

- **Study ID:** 55983006
- **Date:** 2130-10-07 21:22:10
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2130-10-07_21-22-10_s55983006/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2130-10-07_21-22-10_s55983006/756112b0-a6239271-e8d2e395-e2019c21-8bd6a61f.jpg`, `/data/patient/2130-10-07_21-22-10_s55983006/8385af08-8516e6ef-1401e3b8-75199f0d-5e5877e1.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** Chest:  Frontal and lateral views

**INDICATION:** ___M with cough, fever. On immunosuppressants for liver transplant
 // ___M with cough, fever. On immunosuppressants for liver transplant

**TECHNIQUE:** Chest:  Frontal and Lateral

**COMPARISON:** ___ and ___

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