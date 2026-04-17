# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12963531`
- 7 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54527138`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53443143
- **Date:** 2131-08-26 14:20:45
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2131-08-26_14-20-45_s53443143/`
- **Report:** `/data/patient/2131-08-26_14-20-45_s53443143/report.txt`
- **Images:** `/data/patient/2131-08-26_14-20-45_s53443143/41d91119-e4864968-f736d803-6295f4df-29c302ea.jpg`, `/data/patient/2131-08-26_14-20-45_s53443143/fa323a43-287e7b67-e0efec9e-9db65ff2-f6180c57.jpg`

### Prior Study 2: 59369967
- **Date:** 2131-10-12 20:19:05
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , LL
- **Folder:** `/data/patient/2131-10-12_20-19-05_s59369967/`
- **Report:** `/data/patient/2131-10-12_20-19-05_s59369967/report.txt`
- **Images:** `/data/patient/2131-10-12_20-19-05_s59369967/70556779-5d594bd7-7131cbb1-c990fa9a-9a625f61.jpg`, `/data/patient/2131-10-12_20-19-05_s59369967/a5e77ee2-5fec82c7-1f5ffe9c-ccd28c6b-f4a44978.jpg`

### Prior Study 3: 59505688
- **Date:** 2131-10-18 14:51:12
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, LATERAL
- **Folder:** `/data/patient/2131-10-18_14-51-12_s59505688/`
- **Report:** `/data/patient/2131-10-18_14-51-12_s59505688/report.txt`
- **Images:** `/data/patient/2131-10-18_14-51-12_s59505688/0fecd070-24b67744-93fe3cdb-429860a4-386b63f5.jpg`, `/data/patient/2131-10-18_14-51-12_s59505688/44f44165-06ab81a8-b9d0f4c2-2c65e354-bd5cbfbf.jpg`, `/data/patient/2131-10-18_14-51-12_s59505688/5757b72f-454a5bc3-efa625b3-859d88b2-a2bd2112.jpg`

### Prior Study 4: 52085657
- **Date:** 2131-10-19 16:07:44
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2131-10-19_16-07-44_s52085657/`
- **Report:** `/data/patient/2131-10-19_16-07-44_s52085657/report.txt`
- **Images:** `/data/patient/2131-10-19_16-07-44_s52085657/f983cdd1-c3d0de12-3db3f665-cdadb3af-3ffd4c47.jpg`

### Prior Study 5: 57210258
- **Date:** 2132-06-18 01:38:12
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2132-06-18_01-38-12_s57210258/`
- **Report:** `/data/patient/2132-06-18_01-38-12_s57210258/report.txt`
- **Images:** `/data/patient/2132-06-18_01-38-12_s57210258/5f17fe93-aaa0c148-72ccdc7f-ad2268b1-56572a09.jpg`

### Prior Study 6: 50827294
- **Date:** 2133-01-16 01:45:18
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2133-01-16_01-45-18_s50827294/`
- **Report:** `/data/patient/2133-01-16_01-45-18_s50827294/report.txt`
- **Images:** `/data/patient/2133-01-16_01-45-18_s50827294/2f367971-fd362569-13656215-c6b98024-ea2cf207.jpg`, `/data/patient/2133-01-16_01-45-18_s50827294/ddd9741c-9e15a25a-d4b08e32-9ee083c4-b7671def.jpg`

### Prior Study 7: 58929701
- **Date:** 2133-01-18 03:46:32
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2133-01-18_03-46-32_s58929701/`
- **Report:** `/data/patient/2133-01-18_03-46-32_s58929701/report.txt`
- **Images:** `/data/patient/2133-01-18_03-46-32_s58929701/db56399e-4f04b226-d9773c85-a6d565a6-04fe3904.jpg`, `/data/patient/2133-01-18_03-46-32_s58929701/f2fc645a-c9a8eb56-89315f4e-063eed9b-7eccbae9.jpg`

## Target Study

- **Study ID:** 54527138
- **Date:** 2133-02-04 23:04:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2133-02-04_23-04-46_s54527138/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2133-02-04_23-04-46_s54527138/980d5f73-a77d993b-7b3da70b-568e00db-8b84048d.jpg`, `/data/patient/2133-02-04_23-04-46_s54527138/eb52937f-7fa55b40-86540246-ca98fc35-a5a9b68a.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** Right IJ dialysis catheter, evaluate line placement.

**COMPARISON:** Chest radiographs of ___, ___ and ___.

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