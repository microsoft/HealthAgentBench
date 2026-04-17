# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17112432`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `52349735`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 56192054
- **Date:** 2110-09-12 12:27:14
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2110-09-12_12-27-14_s56192054/`
- **Report:** `/data/patient/2110-09-12_12-27-14_s56192054/report.txt`
- **Images:** `/data/patient/2110-09-12_12-27-14_s56192054/d9a018f0-efb2820b-ed7a64b7-c05b8be3-12124812.jpg`

### Prior Study 2: 57935403
- **Date:** 2110-09-13 05:42:50
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2110-09-13_05-42-50_s57935403/`
- **Report:** `/data/patient/2110-09-13_05-42-50_s57935403/report.txt`
- **Images:** `/data/patient/2110-09-13_05-42-50_s57935403/f05b9731-d6bf3b29-6197f242-4cc974a3-fe0f5b56.jpg`

### Prior Study 3: 50407173
- **Date:** 2110-09-16 17:43:07
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2110-09-16_17-43-07_s50407173/`
- **Report:** `/data/patient/2110-09-16_17-43-07_s50407173/report.txt`
- **Images:** `/data/patient/2110-09-16_17-43-07_s50407173/2a0ce644-defed4a1-f1d778d7-8da5ba60-b5d8e243.jpg`, `/data/patient/2110-09-16_17-43-07_s50407173/ebbcd473-0c218cdd-1a652c92-c84c739f-cc9f23f3.jpg`

### Prior Study 4: 59522601
- **Date:** 2110-09-16 09:39:50
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2110-09-16_09-39-50_s59522601/`
- **Report:** `/data/patient/2110-09-16_09-39-50_s59522601/report.txt`
- **Images:** `/data/patient/2110-09-16_09-39-50_s59522601/908fcfa5-90abe83a-27e2b569-6d63788e-3f258290.jpg`, `/data/patient/2110-09-16_09-39-50_s59522601/efe3cdc5-c0ced06a-212a5901-9c1ee7c7-bbbe0e6b.jpg`

### Prior Study 5: 56998267
- **Date:** 2110-09-17 13:20:44
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2110-09-17_13-20-44_s56998267/`
- **Report:** `/data/patient/2110-09-17_13-20-44_s56998267/report.txt`
- **Images:** `/data/patient/2110-09-17_13-20-44_s56998267/be319f71-2b1ab302-55580f5d-ffc6e9e0-9e90689a.jpg`, `/data/patient/2110-09-17_13-20-44_s56998267/e00dbd13-be46d17d-a9d11aa6-fe69dec2-7ccc308a.jpg`

## Target Study

- **Study ID:** 52349735
- **Date:** 2110-10-05 11:32:39
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2110-10-05_11-32-39_s52349735/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2110-10-05_11-32-39_s52349735/7e7b19ac-d29aedbe-10d9f138-4037688a-57615f21.jpg`, `/data/patient/2110-10-05_11-32-39_s52349735/fd2b67dc-f8167506-7c0667ac-33d49ad7-cc9fbde1.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old man with multiple rib fractures.  Please evaluate
 fractures.

**COMPARISON:** Chest radiograph ___ and CT ___.

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