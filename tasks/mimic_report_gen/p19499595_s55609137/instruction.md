# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `19499595`
- 12 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55609137`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59466886
- **Date:** 2139-10-08 12:37:06
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2139-10-08_12-37-06_s59466886/`
- **Report:** `/data/patient/2139-10-08_12-37-06_s59466886/report.txt`
- **Images:** `/data/patient/2139-10-08_12-37-06_s59466886/361f3292-69c09716-56d735d9-af2502ee-6ba5bfcf.jpg`, `/data/patient/2139-10-08_12-37-06_s59466886/d0f12959-3ddcfd01-600a8d75-bd545bef-1655affe.jpg`

### Prior Study 2: 58099159
- **Date:** 2140-08-13 23:49:09
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2140-08-13_23-49-09_s58099159/`
- **Report:** `/data/patient/2140-08-13_23-49-09_s58099159/report.txt`
- **Images:** `/data/patient/2140-08-13_23-49-09_s58099159/cf85ad05-11574785-5d5c24bc-5931200b-df7f068a.jpg`, `/data/patient/2140-08-13_23-49-09_s58099159/dcc0c992-a044f70a-770a63e9-ea13d7b4-b62a671a.jpg`

### Prior Study 3: 57088454
- **Date:** 2141-03-28 20:49:43
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2141-03-28_20-49-43_s57088454/`
- **Report:** `/data/patient/2141-03-28_20-49-43_s57088454/report.txt`
- **Images:** `/data/patient/2141-03-28_20-49-43_s57088454/2a41d909-c858a5fc-da024f8f-a33bd3ff-ed8fe748.jpg`, `/data/patient/2141-03-28_20-49-43_s57088454/6eb90215-8ba4b024-b326c41b-9e832fd5-d678690f.jpg`, `/data/patient/2141-03-28_20-49-43_s57088454/faafd86d-6a1d4047-0cf76260-da7b281c-eba9d436.jpg`

### Prior Study 4: 56713351
- **Date:** 2141-12-02 13:35:57
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2141-12-02_13-35-57_s56713351/`
- **Report:** `/data/patient/2141-12-02_13-35-57_s56713351/report.txt`
- **Images:** `/data/patient/2141-12-02_13-35-57_s56713351/c1d95317-261068b4-1cfb7863-12882166-269c307b.jpg`, `/data/patient/2141-12-02_13-35-57_s56713351/db395251-352c94c2-fcee5f77-85922f20-33f7f530.jpg`

### Prior Study 5: 58177798
- **Date:** 2141-12-07 13:53:17
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2141-12-07_13-53-17_s58177798/`
- **Report:** `/data/patient/2141-12-07_13-53-17_s58177798/report.txt`
- **Images:** `/data/patient/2141-12-07_13-53-17_s58177798/1b3502f6-703cfde6-fe24a195-2a059f09-8e715e77.jpg`, `/data/patient/2141-12-07_13-53-17_s58177798/9b8c8c16-1ff93d63-c49fdc62-8256171e-4c4acb9d.jpg`

### Prior Study 6: 55937788
- **Date:** 2142-02-06 12:05:48
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2142-02-06_12-05-48_s55937788/`
- **Report:** `/data/patient/2142-02-06_12-05-48_s55937788/report.txt`
- **Images:** `/data/patient/2142-02-06_12-05-48_s55937788/2290a4bd-134ecd43-8b4207a5-bc940915-b81657b2.jpg`, `/data/patient/2142-02-06_12-05-48_s55937788/af0c4020-5add1573-1c5ab2bf-de56409e-b3748c43.jpg`

### Prior Study 7: 51712579
- **Date:** 2142-05-16 20:57:00
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2142-05-16_20-57-00_s51712579/`
- **Report:** `/data/patient/2142-05-16_20-57-00_s51712579/report.txt`
- **Images:** `/data/patient/2142-05-16_20-57-00_s51712579/7ddbb51e-55d7dd8d-8627c186-c5bc068b-ddb034e8.jpg`, `/data/patient/2142-05-16_20-57-00_s51712579/cbcc7f2d-85037ab8-b4a6295b-36cbbacc-09003a12.jpg`

### Prior Study 8: 57517941
- **Date:** 2142-05-24 14:29:15
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2142-05-24_14-29-15_s57517941/`
- **Report:** `/data/patient/2142-05-24_14-29-15_s57517941/report.txt`
- **Images:** `/data/patient/2142-05-24_14-29-15_s57517941/4c9812bf-f392e749-e5a9e763-24de2d49-20271034.jpg`

### Prior Study 9: 51527425
- **Date:** 2142-06-12 18:29:11
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2142-06-12_18-29-11_s51527425/`
- **Report:** `/data/patient/2142-06-12_18-29-11_s51527425/report.txt`
- **Images:** `/data/patient/2142-06-12_18-29-11_s51527425/83c03ab3-cb2d1377-2e09bc4f-26e7f47e-67901270.jpg`, `/data/patient/2142-06-12_18-29-11_s51527425/84dac834-d9f40739-755532a0-1ddab50a-cae07005.jpg`

### Prior Study 10: 59685259
- **Date:** 2142-11-14 14:59:10
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2142-11-14_14-59-10_s59685259/`
- **Report:** `/data/patient/2142-11-14_14-59-10_s59685259/report.txt`
- **Images:** `/data/patient/2142-11-14_14-59-10_s59685259/177a1056-691824d9-0baad023-32217305-9f282e25.jpg`, `/data/patient/2142-11-14_14-59-10_s59685259/553f6199-37bc0e92-8f246bbd-f36f847e-8d0c8e14.jpg`

### Prior Study 11: 57390903
- **Date:** 2143-07-14 17:28:47
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2143-07-14_17-28-47_s57390903/`
- **Report:** `/data/patient/2143-07-14_17-28-47_s57390903/report.txt`
- **Images:** `/data/patient/2143-07-14_17-28-47_s57390903/87121059-41c650c2-009d026d-25bb56aa-f6ddee27.jpg`, `/data/patient/2143-07-14_17-28-47_s57390903/8f866521-2083f0bb-a12df756-24346ecd-5e484e40.jpg`

### Prior Study 12: 52825626
- **Date:** 2143-10-12 23:06:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2143-10-12_23-06-46_s52825626/`
- **Report:** `/data/patient/2143-10-12_23-06-46_s52825626/report.txt`
- **Images:** `/data/patient/2143-10-12_23-06-46_s52825626/00dbc849-560058de-e051c029-8cd120fe-9a4f3202.jpg`, `/data/patient/2143-10-12_23-06-46_s52825626/231686e2-a4e00674-f79b0a9d-3aa8362f-c822c78a.jpg`

## Target Study

- **Study ID:** 55609137
- **Date:** 2144-08-04 19:11:57
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2144-08-04_19-11-57_s55609137/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2144-08-04_19-11-57_s55609137/90959c50-71b7d860-9e648092-e311c647-681c62e5.jpg`, `/data/patient/2144-08-04_19-11-57_s55609137/c04f1959-6d763649-3561d2d3-baf924f7-bac2214b.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (AP AND LAT)

**INDICATION:** ___ year old woman with acute change in mental status, h/o
 parkinsonism and dysphagia

**COMPARISON:** ___

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