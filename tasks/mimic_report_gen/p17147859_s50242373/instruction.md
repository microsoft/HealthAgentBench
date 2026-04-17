# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17147859`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50242373`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59519248
- **Date:** 2196-06-29 12:36:24
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2196-06-29_12-36-24_s59519248/`
- **Report:** `/data/patient/2196-06-29_12-36-24_s59519248/report.txt`
- **Images:** `/data/patient/2196-06-29_12-36-24_s59519248/1129d3bb-924babcc-6bcb3caf-4a76b42e-b4b64f89.jpg`, `/data/patient/2196-06-29_12-36-24_s59519248/ae93b9d8-d3f07b0f-2acf2351-9a51b459-bfb724fb.jpg`

### Prior Study 2: 55301691
- **Date:** 2197-01-10 16:10:24
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2197-01-10_16-10-24_s55301691/`
- **Report:** `/data/patient/2197-01-10_16-10-24_s55301691/report.txt`
- **Images:** `/data/patient/2197-01-10_16-10-24_s55301691/af9b5e5b-573301f2-71ea7f54-300d7537-be08d760.jpg`, `/data/patient/2197-01-10_16-10-24_s55301691/d8f6df8b-a89ccea2-63bada22-1566fcf0-126ceeb7.jpg`

### Prior Study 3: 56619225
- **Date:** 2200-02-24 16:48:26
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2200-02-24_16-48-26_s56619225/`
- **Report:** `/data/patient/2200-02-24_16-48-26_s56619225/report.txt`
- **Images:** `/data/patient/2200-02-24_16-48-26_s56619225/8146d764-df8a61cc-05eee7e7-2a09b0ca-af854e29.jpg`, `/data/patient/2200-02-24_16-48-26_s56619225/c476c50a-1f0890c2-aba98995-954a758b-7f46da68.jpg`

### Prior Study 4: 52077543
- **Date:** 2200-03-17 17:49:51
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2200-03-17_17-49-51_s52077543/`
- **Report:** `/data/patient/2200-03-17_17-49-51_s52077543/report.txt`
- **Images:** `/data/patient/2200-03-17_17-49-51_s52077543/b6ce62d8-12124de8-769cb0d0-07e96bef-ca38036d.jpg`, `/data/patient/2200-03-17_17-49-51_s52077543/b763b37f-bcd8f18b-d2041837-3b2722d1-f6f3013a.jpg`

### Prior Study 5: 52321096
- **Date:** 2200-12-18 12:21:32
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2200-12-18_12-21-32_s52321096/`
- **Report:** `/data/patient/2200-12-18_12-21-32_s52321096/report.txt`
- **Images:** `/data/patient/2200-12-18_12-21-32_s52321096/729e2a72-abdbd01c-884f4185-7fb1ac97-9dfe808c.jpg`, `/data/patient/2200-12-18_12-21-32_s52321096/e8a8bd48-feafd477-16f9cfa0-575478d2-bc2c5cbb.jpg`

## Target Study

- **Study ID:** 50242373
- **Date:** 2201-01-16 10:41:54
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2201-01-16_10-41-54_s50242373/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2201-01-16_10-41-54_s50242373/3ceaa65b-850c135e-da080f5d-e28c2bc7-a9dea924.jpg`, `/data/patient/2201-01-16_10-41-54_s50242373/60df340a-31a5266d-2f3912a7-3758a59c-9a5baa79.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** PA and lateral chest radiographs.

**INDICATION:** ___-year-old woman with chest pain.  Evaluate for an acute
 process.

**TECHNIQUE:** Chest PA and lateral.

**COMPARISON:** Chest radiograph from ___.

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