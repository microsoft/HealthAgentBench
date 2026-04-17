# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17163861`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56902932`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 55133499
- **Date:** 2150-05-26 01:03:10
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2150-05-26_01-03-10_s55133499/`
- **Report:** `/data/patient/2150-05-26_01-03-10_s55133499/report.txt`
- **Images:** `/data/patient/2150-05-26_01-03-10_s55133499/bd8fc3e9-687db5d6-574cb5a6-b78d18b2-2f5fb4de.jpg`, `/data/patient/2150-05-26_01-03-10_s55133499/db0c967e-30c9c887-b4196fb7-e0ba8546-1b9ad52e.jpg`

### Prior Study 2: 51731956
- **Date:** 2150-05-28 14:11:33
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2150-05-28_14-11-33_s51731956/`
- **Report:** `/data/patient/2150-05-28_14-11-33_s51731956/report.txt`
- **Images:** `/data/patient/2150-05-28_14-11-33_s51731956/354f8abd-01f7f413-cb068ad1-1d47c651-7a17c514.jpg`, `/data/patient/2150-05-28_14-11-33_s51731956/af4526a3-ed45d1ae-28409d1f-a7389574-8e977011.jpg`

### Prior Study 3: 50065267
- **Date:** 2150-06-03 17:17:12
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, AP, LATERAL
- **Folder:** `/data/patient/2150-06-03_17-17-12_s50065267/`
- **Report:** `/data/patient/2150-06-03_17-17-12_s50065267/report.txt`
- **Images:** `/data/patient/2150-06-03_17-17-12_s50065267/1f13c4be-a6bc48a6-5675f256-e95b8a28-c017e780.jpg`, `/data/patient/2150-06-03_17-17-12_s50065267/3d93e17d-7634fb78-ec7abdcd-a745490f-6eb6cc24.jpg`, `/data/patient/2150-06-03_17-17-12_s50065267/83502e58-5ada1fba-450984b0-07c9ec9e-2b5b91b4.jpg`, `/data/patient/2150-06-03_17-17-12_s50065267/bd3dc01c-c67b8f05-580c3880-de7352aa-4118828e.jpg`

### Prior Study 4: 56013519
- **Date:** 2151-08-17 14:36:04
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2151-08-17_14-36-04_s56013519/`
- **Report:** `/data/patient/2151-08-17_14-36-04_s56013519/report.txt`
- **Images:** `/data/patient/2151-08-17_14-36-04_s56013519/0f513599-eb6bddc9-4306d15d-46c7c0c2-a3c6c854.jpg`, `/data/patient/2151-08-17_14-36-04_s56013519/de7f2739-8c743a3a-6e0e37fb-635c58f5-a48a0ab7.jpg`

### Prior Study 5: 52169517
- **Date:** 2151-11-14 04:47:58
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL, PA
- **Folder:** `/data/patient/2151-11-14_04-47-58_s52169517/`
- **Report:** `/data/patient/2151-11-14_04-47-58_s52169517/report.txt`
- **Images:** `/data/patient/2151-11-14_04-47-58_s52169517/2ee8335e-c2cee8be-256455f2-9cc54604-d6b4c10d.jpg`, `/data/patient/2151-11-14_04-47-58_s52169517/a9493b3c-4d63defd-55b09266-3147f2af-e73caba1.jpg`, `/data/patient/2151-11-14_04-47-58_s52169517/dd7f3873-773c451c-3500ff51-f62851f4-3a6116a9.jpg`

### Prior Study 6: 51599732
- **Date:** 2153-01-30 21:54:48
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2153-01-30_21-54-48_s51599732/`
- **Report:** `/data/patient/2153-01-30_21-54-48_s51599732/report.txt`
- **Images:** `/data/patient/2153-01-30_21-54-48_s51599732/7af50fb4-7220f1e6-2f232aa7-bdbbc51c-18f1c512.jpg`, `/data/patient/2153-01-30_21-54-48_s51599732/c2d5f938-8ac36872-dfac1b06-126c490e-6f63e582.jpg`

## Target Study

- **Study ID:** 56902932
- **Date:** 2154-01-30 18:26:52
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2154-01-30_18-26-52_s56902932/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2154-01-30_18-26-52_s56902932/4e2deb58-2087d69f-a4c1a7c8-776af924-1bd0202d.jpg`, `/data/patient/2154-01-30_18-26-52_s56902932/cafde7cd-b6e7a873-406f5371-358aca60-ed02bdc3.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___M weakness, please evaluate for cardiopulmonary change  // ___M
 weakness, please evaluate for cardiopulmonary change

**TECHNIQUE:** PA and lateral views of the chest.

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