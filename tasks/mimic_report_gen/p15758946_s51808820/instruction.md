# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15758946`
- 11 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51808820`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 50020371
- **Date:** 2199-01-01 09:29:57
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2199-01-01_09-29-57_s50020371/`
- **Report:** `/data/patient/2199-01-01_09-29-57_s50020371/report.txt`
- **Images:** `/data/patient/2199-01-01_09-29-57_s50020371/5e861703-66367757-f8a458b6-39741594-3ab89d41.jpg`, `/data/patient/2199-01-01_09-29-57_s50020371/a767b7c0-6bdaee42-8ca0cd60-7b89ffb1-3bbbba27.jpg`

### Prior Study 2: 58167653
- **Date:** 2199-01-30 12:55:52
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-01-30_12-55-52_s58167653/`
- **Report:** `/data/patient/2199-01-30_12-55-52_s58167653/report.txt`
- **Images:** `/data/patient/2199-01-30_12-55-52_s58167653/3beddebe-77318989-f0a94514-750bd4e3-c009749d.jpg`

### Prior Study 3: 52981971
- **Date:** 2199-01-30 20:25:38
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-01-30_20-25-38_s52981971/`
- **Report:** `/data/patient/2199-01-30_20-25-38_s52981971/report.txt`
- **Images:** `/data/patient/2199-01-30_20-25-38_s52981971/b2f5bef1-dc067a8c-521f6348-16787841-eb270634.jpg`

### Prior Study 4: 50697229
- **Date:** 2199-01-31 05:28:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-01-31_05-28-06_s50697229/`
- **Report:** `/data/patient/2199-01-31_05-28-06_s50697229/report.txt`
- **Images:** `/data/patient/2199-01-31_05-28-06_s50697229/be78e28d-1c76d439-9b5e832e-b0935ea9-62e6cf91.jpg`

### Prior Study 5: 55901243
- **Date:** 2199-02-01 06:11:44
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-01_06-11-44_s55901243/`
- **Report:** `/data/patient/2199-02-01_06-11-44_s55901243/report.txt`
- **Images:** `/data/patient/2199-02-01_06-11-44_s55901243/f329badd-5f934b2d-44503f43-93b04e89-810e8f0c.jpg`

### Prior Study 6: 51850726
- **Date:** 2199-02-02 07:45:56
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-02_07-45-56_s51850726/`
- **Report:** `/data/patient/2199-02-02_07-45-56_s51850726/report.txt`
- **Images:** `/data/patient/2199-02-02_07-45-56_s51850726/bb2896e3-7eeb9cba-9b026443-c0ee46b8-694ab8ed.jpg`

### Prior Study 7: 56167449
- **Date:** 2199-02-03 04:53:58
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-03_04-53-58_s56167449/`
- **Report:** `/data/patient/2199-02-03_04-53-58_s56167449/report.txt`
- **Images:** `/data/patient/2199-02-03_04-53-58_s56167449/97e428ce-51d4215e-210ed55c-4327be47-4a10e46c.jpg`

### Prior Study 8: 57083382
- **Date:** 2199-02-04 05:01:55
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-04_05-01-55_s57083382/`
- **Report:** `/data/patient/2199-02-04_05-01-55_s57083382/report.txt`
- **Images:** `/data/patient/2199-02-04_05-01-55_s57083382/9f5b44e9-6f162589-6533517c-f73c712d-9cef61a7.jpg`

### Prior Study 9: 59924609
- **Date:** 2199-02-05 05:17:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-05_05-17-06_s59924609/`
- **Report:** `/data/patient/2199-02-05_05-17-06_s59924609/report.txt`
- **Images:** `/data/patient/2199-02-05_05-17-06_s59924609/f92f8eca-d4526790-a1842ee9-1c5b4666-a0e18256.jpg`

### Prior Study 10: 57586513
- **Date:** 2199-02-06 05:15:52
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-06_05-15-52_s57586513/`
- **Report:** `/data/patient/2199-02-06_05-15-52_s57586513/report.txt`
- **Images:** `/data/patient/2199-02-06_05-15-52_s57586513/15a43747-b7f52373-15c7623d-8ec7b6f7-c1fd59aa.jpg`

### Prior Study 11: 56618601
- **Date:** 2199-02-07 05:05:30
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-07_05-05-30_s56618601/`
- **Report:** `/data/patient/2199-02-07_05-05-30_s56618601/report.txt`
- **Images:** `/data/patient/2199-02-07_05-05-30_s56618601/dbbd8ca0-a3e78630-061e92f4-cc6ea2d3-05314ad2.jpg`

## Target Study

- **Study ID:** 51808820
- **Date:** 2199-02-10 05:04:10
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2199-02-10_05-04-10_s51808820/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2199-02-10_05-04-10_s51808820/35d6d97a-9cbb9f6a-78b7bf1d-f7a49df3-fa17a2b5.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** ___-year-old female with AFib with rapid ventricular response.
 
 STUDY:  Portable AP upright chest radiograph.

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