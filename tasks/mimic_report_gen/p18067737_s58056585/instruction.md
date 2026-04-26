# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `18067737`
- 8 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `58056585`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58001075
- **Date:** 2176-12-29 14:18:25
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, PA, LATERAL
- **Folder:** `/data/patient/2176-12-29_14-18-25_s58001075/`
- **Report:** `/data/patient/2176-12-29_14-18-25_s58001075/report.txt`
- **Images:** `/data/patient/2176-12-29_14-18-25_s58001075/1ed95e47-83a54489-79ebd823-db934045-acd7ca23.jpg`, `/data/patient/2176-12-29_14-18-25_s58001075/33bd9626-0ea91dc1-d8b6449a-1b20afcb-19da17f2.jpg`, `/data/patient/2176-12-29_14-18-25_s58001075/8faff40c-536b8347-b1b760e0-182dc706-77835a8e.jpg`, `/data/patient/2176-12-29_14-18-25_s58001075/de01c9bf-3fb74041-71495a3e-efd82101-cace2aa7.jpg`

### Prior Study 2: 56427859
- **Date:** 2177-01-05 19:55:30
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2177-01-05_19-55-30_s56427859/`
- **Report:** `/data/patient/2177-01-05_19-55-30_s56427859/report.txt`
- **Images:** `/data/patient/2177-01-05_19-55-30_s56427859/805c8f03-c6d068dd-c95f546c-e1dfe872-324866d0.jpg`

### Prior Study 3: 58232231
- **Date:** 2177-01-10 18:26:59
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2177-01-10_18-26-59_s58232231/`
- **Report:** `/data/patient/2177-01-10_18-26-59_s58232231/report.txt`
- **Images:** `/data/patient/2177-01-10_18-26-59_s58232231/5dd97738-76c3ff89-82388c36-9f34d2c3-5073e305.jpg`, `/data/patient/2177-01-10_18-26-59_s58232231/f33df19b-40b70f49-e2089e24-af20049c-136fb213.jpg`

### Prior Study 4: 57632806
- **Date:** 2177-01-22 14:07:40
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2177-01-22_14-07-40_s57632806/`
- **Report:** `/data/patient/2177-01-22_14-07-40_s57632806/report.txt`
- **Images:** `/data/patient/2177-01-22_14-07-40_s57632806/837cc5b5-e15e87de-3fc53c74-c391e8b0-c7e53396.jpg`, `/data/patient/2177-01-22_14-07-40_s57632806/e51549cd-cbebd9a4-0aeaabab-5fa2f8bd-b76c2577.jpg`

### Prior Study 5: 50431066
- **Date:** 2177-02-07 15:14:07
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, PA, LATERAL
- **Folder:** `/data/patient/2177-02-07_15-14-07_s50431066/`
- **Report:** `/data/patient/2177-02-07_15-14-07_s50431066/report.txt`
- **Images:** `/data/patient/2177-02-07_15-14-07_s50431066/404dfc42-ee2b7f16-1f8535c6-eddf267e-b9f928e0.jpg`, `/data/patient/2177-02-07_15-14-07_s50431066/94f5ba63-5b0649c0-63f21058-2429a6c1-291139cc.jpg`, `/data/patient/2177-02-07_15-14-07_s50431066/a6dc99c7-6d793ce2-188bd506-b751deab-79f8ebbb.jpg`, `/data/patient/2177-02-07_15-14-07_s50431066/f90437b8-3b33ff29-c06a7caf-299995e5-2da5c2ba.jpg`

### Prior Study 6: 53583954
- **Date:** 2177-02-18 15:07:38
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2177-02-18_15-07-38_s53583954/`
- **Report:** `/data/patient/2177-02-18_15-07-38_s53583954/report.txt`
- **Images:** `/data/patient/2177-02-18_15-07-38_s53583954/0efbdb11-4a6e04cf-2acc8b02-8b0ee7b6-36a1e507.jpg`

### Prior Study 7: 51465438
- **Date:** 2177-02-21 13:28:32
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2177-02-21_13-28-32_s51465438/`
- **Report:** `/data/patient/2177-02-21_13-28-32_s51465438/report.txt`
- **Images:** `/data/patient/2177-02-21_13-28-32_s51465438/63ee3ff5-d84abed7-10208fcd-96b68026-bb55b8ff.jpg`

### Prior Study 8: 58327706
- **Date:** 2177-06-05 11:27:27
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL, PA
- **Folder:** `/data/patient/2177-06-05_11-27-27_s58327706/`
- **Report:** `/data/patient/2177-06-05_11-27-27_s58327706/report.txt`
- **Images:** `/data/patient/2177-06-05_11-27-27_s58327706/84fdafc6-cb74b0f4-e01856b1-7af27b87-3d01f692.jpg`, `/data/patient/2177-06-05_11-27-27_s58327706/9679cd55-37b997e0-0205c229-df3216c2-705327c9.jpg`, `/data/patient/2177-06-05_11-27-27_s58327706/b973beee-a64f055b-a96181c0-05105bc5-25dcc796.jpg`

## Target Study

- **Study ID:** 58056585
- **Date:** 2177-07-03 17:35:00
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2177-07-03_17-35-00_s58056585/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2177-07-03_17-35-00_s58056585/140516cd-0a4265d2-ce7c8e15-37036b48-42fd24d5.jpg`, `/data/patient/2177-07-03_17-35-00_s58056585/5ad6463b-b79f3447-bf9c7db1-e6fc6f3e-da500463.jpg`, `/data/patient/2177-07-03_17-35-00_s58056585/ce6c73a2-bfbdbdf8-f7f014a2-bfffc5e3-232d2d80.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

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