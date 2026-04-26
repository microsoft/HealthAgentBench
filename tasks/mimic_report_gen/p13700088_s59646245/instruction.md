# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13700088`
- 8 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `59646245`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59542064
- **Date:** 2203-06-02 17:32:42
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2203-06-02_17-32-42_s59542064/`
- **Report:** `/data/patient/2203-06-02_17-32-42_s59542064/report.txt`
- **Images:** `/data/patient/2203-06-02_17-32-42_s59542064/44265749-00dd7405-287e7f77-b68607f3-663cc2f7.jpg`

### Prior Study 2: 51819517
- **Date:** 2203-06-02 17:57:25
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2203-06-02_17-57-25_s51819517/`
- **Report:** `/data/patient/2203-06-02_17-57-25_s51819517/report.txt`
- **Images:** `/data/patient/2203-06-02_17-57-25_s51819517/2b48fff3-ec94225d-0c7dc92c-383e271f-ff7c44bd.jpg`

### Prior Study 3: 53970354
- **Date:** 2203-06-04 06:05:27
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2203-06-04_06-05-27_s53970354/`
- **Report:** `/data/patient/2203-06-04_06-05-27_s53970354/report.txt`
- **Images:** `/data/patient/2203-06-04_06-05-27_s53970354/dda5719b-c91a5364-ffb7de98-16adf278-3aac7099.jpg`

### Prior Study 4: 55908245
- **Date:** 2203-06-14 14:01:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2203-06-14_14-01-46_s55908245/`
- **Report:** `/data/patient/2203-06-14_14-01-46_s55908245/report.txt`
- **Images:** `/data/patient/2203-06-14_14-01-46_s55908245/3c13fcf9-f4e94af1-bd429b2a-ff94e888-09fb67fa.jpg`, `/data/patient/2203-06-14_14-01-46_s55908245/b8a682a3-13005580-762d54e7-031106db-9c766de1.jpg`, `/data/patient/2203-06-14_14-01-46_s55908245/c8f77e9b-ae1d0935-5fc5b81a-bbae4b84-91567aec.jpg`

### Prior Study 5: 52081127
- **Date:** 2203-06-14 16:26:41
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2203-06-14_16-26-41_s52081127/`
- **Report:** `/data/patient/2203-06-14_16-26-41_s52081127/report.txt`
- **Images:** `/data/patient/2203-06-14_16-26-41_s52081127/9f5e6fe5-3058dc34-5fb44a44-687509a4-af7f886f.jpg`

### Prior Study 6: 57798512
- **Date:** 2203-06-14 18:22:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2203-06-14_18-22-03_s57798512/`
- **Report:** `/data/patient/2203-06-14_18-22-03_s57798512/report.txt`
- **Images:** `/data/patient/2203-06-14_18-22-03_s57798512/7502e61e-9548ae94-78e53cb0-47f06975-6a4a0cd6.jpg`

### Prior Study 7: 58916510
- **Date:** 2204-03-03 15:17:08
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2204-03-03_15-17-08_s58916510/`
- **Report:** `/data/patient/2204-03-03_15-17-08_s58916510/report.txt`
- **Images:** `/data/patient/2204-03-03_15-17-08_s58916510/0df3aaa4-28257f4c-e142fab8-bbea28fb-0e313b9d.jpg`, `/data/patient/2204-03-03_15-17-08_s58916510/6f76af94-e325cbe7-266c1d35-9c931f0e-e0a1a2b5.jpg`

### Prior Study 8: 54082940
- **Date:** 2204-03-08 22:56:54
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2204-03-08_22-56-54_s54082940/`
- **Report:** `/data/patient/2204-03-08_22-56-54_s54082940/report.txt`
- **Images:** `/data/patient/2204-03-08_22-56-54_s54082940/4b8a29ae-36006b7b-c4964368-02ab587d-1ee25fdc.jpg`, `/data/patient/2204-03-08_22-56-54_s54082940/a0a7577d-53a8748e-450244b3-39cec864-8a18f0cf.jpg`

## Target Study

- **Study ID:** 59646245
- **Date:** 2204-07-29 13:04:47
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2204-07-29_13-04-47_s59646245/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2204-07-29_13-04-47_s59646245/11b51e2b-5c48db12-3faeaf40-aaf27ca7-a6be3ce9.jpg`, `/data/patient/2204-07-29_13-04-47_s59646245/8ce33378-337bc3e6-2915b9bf-0ea16f16-2c986cfe.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** ___-year-old female with weakness.

**COMPARISON:** Comparison is made with chest radiographs from ___
 and ___.

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