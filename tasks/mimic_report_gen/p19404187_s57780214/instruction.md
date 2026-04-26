# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `19404187`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `57780214`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59383411
- **Date:** 2199-04-25 13:43:55
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-04-25_13-43-55_s59383411/`
- **Report:** `/data/patient/2199-04-25_13-43-55_s59383411/report.txt`
- **Images:** `/data/patient/2199-04-25_13-43-55_s59383411/9c428194-407d67aa-d8f7441b-6010da36-1768a83e.jpg`

### Prior Study 2: 50682888
- **Date:** 2199-05-01 19:22:31
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2199-05-01_19-22-31_s50682888/`
- **Report:** `/data/patient/2199-05-01_19-22-31_s50682888/report.txt`
- **Images:** `/data/patient/2199-05-01_19-22-31_s50682888/08da513d-5325ee2d-d57746d8-762cf929-bf1c0fa4.jpg`, `/data/patient/2199-05-01_19-22-31_s50682888/847237ae-40229169-b1a8c3fd-04d45b62-fc0cee14.jpg`

### Prior Study 3: 51682045
- **Date:** 2199-05-18 05:22:36
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2199-05-18_05-22-36_s51682045/`
- **Report:** `/data/patient/2199-05-18_05-22-36_s51682045/report.txt`
- **Images:** `/data/patient/2199-05-18_05-22-36_s51682045/64b8ecd0-558bc928-d94477cd-e5066ca7-44e87fb5.jpg`

### Prior Study 4: 51734751
- **Date:** 2199-05-19 13:40:47
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2199-05-19_13-40-47_s51734751/`
- **Report:** `/data/patient/2199-05-19_13-40-47_s51734751/report.txt`
- **Images:** `/data/patient/2199-05-19_13-40-47_s51734751/d117e730-3cff0d3b-d5cfdaa4-3021811d-adc0d61c.jpg`

### Prior Study 5: 53864144
- **Date:** 2199-05-19 15:07:17
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2199-05-19_15-07-17_s53864144/`
- **Report:** `/data/patient/2199-05-19_15-07-17_s53864144/report.txt`
- **Images:** `/data/patient/2199-05-19_15-07-17_s53864144/ae57041e-ad6150ec-9dbf82b5-633feb0e-de440528.jpg`

### Prior Study 6: 58274681
- **Date:** 2199-05-27 15:39:51
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2199-05-27_15-39-51_s58274681/`
- **Report:** `/data/patient/2199-05-27_15-39-51_s58274681/report.txt`
- **Images:** `/data/patient/2199-05-27_15-39-51_s58274681/2105a3d5-135b0241-ad3232b4-24f593cc-3d0862a6.jpg`, `/data/patient/2199-05-27_15-39-51_s58274681/c408021c-9ec7e58b-9e1623a5-ea612873-9f6462aa.jpg`

## Target Study

- **Study ID:** 57780214
- **Date:** 2199-06-30 10:48:39
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2199-06-30_10-48-39_s57780214/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2199-06-30_10-48-39_s57780214/480f169c-15ef13a4-4ca3b85d-181a240e-edc79169.jpg`, `/data/patient/2199-06-30_10-48-39_s57780214/cdd7ee52-66082b29-febaceb1-6ced7608-1e8e8631.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Aspiration following EGD.  Concern for pneumonia.

**TECHNIQUE:** PA and lateral chest radiographs.

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