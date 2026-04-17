# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13450581`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `53158366`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 57882993
- **Date:** 2183-05-01 08:58:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2183-05-01_08-58-18_s57882993/`
- **Report:** `/data/patient/2183-05-01_08-58-18_s57882993/report.txt`
- **Images:** `/data/patient/2183-05-01_08-58-18_s57882993/b5b08344-1a02337d-90a42a3b-cf710862-a4ff491d.jpg`, `/data/patient/2183-05-01_08-58-18_s57882993/f39a0cd8-fb45cb6e-63f5fa30-21668913-0ac228d3.jpg`

### Prior Study 2: 59529409
- **Date:** 2183-08-17 11:49:49
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2183-08-17_11-49-49_s59529409/`
- **Report:** `/data/patient/2183-08-17_11-49-49_s59529409/report.txt`
- **Images:** `/data/patient/2183-08-17_11-49-49_s59529409/8ab13ae3-2d580227-ac6e610c-f2e5c694-60d57d41.jpg`

### Prior Study 3: 53613536
- **Date:** 2183-09-16 14:08:34
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2183-09-16_14-08-34_s53613536/`
- **Report:** `/data/patient/2183-09-16_14-08-34_s53613536/report.txt`
- **Images:** `/data/patient/2183-09-16_14-08-34_s53613536/ce26e6f2-6bff880c-7e350e95-0571671b-15e0c25b.jpg`

### Prior Study 4: 51153135
- **Date:** 2185-04-02 13:56:13
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2185-04-02_13-56-13_s51153135/`
- **Report:** `/data/patient/2185-04-02_13-56-13_s51153135/report.txt`
- **Images:** `/data/patient/2185-04-02_13-56-13_s51153135/842c80c2-40a8d117-9d30e18e-4548b4b6-99f871ed.jpg`, `/data/patient/2185-04-02_13-56-13_s51153135/a27d6353-c65e4d61-f0312644-18f75864-525a1543.jpg`

### Prior Study 5: 52299675
- **Date:** 2185-04-02 17:40:11
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2185-04-02_17-40-11_s52299675/`
- **Report:** `/data/patient/2185-04-02_17-40-11_s52299675/report.txt`
- **Images:** `/data/patient/2185-04-02_17-40-11_s52299675/1f3770d8-292e129a-67319735-0573718a-8fcb1e31.jpg`

### Prior Study 6: 50580104
- **Date:** 2185-12-03 22:40:38
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2185-12-03_22-40-38_s50580104/`
- **Report:** `/data/patient/2185-12-03_22-40-38_s50580104/report.txt`
- **Images:** `/data/patient/2185-12-03_22-40-38_s50580104/92a1d719-e7404cd8-e6e9d5c1-fce29388-120afc34.jpg`, `/data/patient/2185-12-03_22-40-38_s50580104/bf732fa8-e739d288-c19041d7-eb81cf9c-de266f79.jpg`

## Target Study

- **Study ID:** 53158366
- **Date:** 2186-11-10 14:09:42
- **Procedure:** Performed Desc
- **Views:** LL, , , LL
- **Folder:** `/data/patient/2186-11-10_14-09-42_s53158366/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2186-11-10_14-09-42_s53158366/0973f2e4-fd436409-ac1ae199-94dae0f7-7ed0d26a.jpg`, `/data/patient/2186-11-10_14-09-42_s53158366/43a15b39-91e19d8c-aa4bf7b9-1f192be3-ad880dd8.jpg`, `/data/patient/2186-11-10_14-09-42_s53158366/b774b7cb-d6e72a35-c85f2601-161e02e1-de195f8f.jpg`, `/data/patient/2186-11-10_14-09-42_s53158366/dec8fc17-025db48c-c1db3442-ee663d79-8d57b392.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___ year old man with L shoulder pain, known mass L upper lone on
 pet scan, ?bigger.  // ?L upper lobe mass

**TECHNIQUE:** Chest PA and lateral

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