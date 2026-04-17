# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17337033`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56541072`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58080029
- **Date:** 2185-12-20 16:35:09
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2185-12-20_16-35-09_s58080029/`
- **Report:** `/data/patient/2185-12-20_16-35-09_s58080029/report.txt`
- **Images:** `/data/patient/2185-12-20_16-35-09_s58080029/3f88d0d6-bcbb5cb4-27d9e806-7b3903f8-2645e762.jpg`

### Prior Study 2: 51074951
- **Date:** 2186-08-23 12:38:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2186-08-23_12-38-03_s51074951/`
- **Report:** `/data/patient/2186-08-23_12-38-03_s51074951/report.txt`
- **Images:** `/data/patient/2186-08-23_12-38-03_s51074951/5b3a073e-8c070064-383e87bc-900d5646-a15c9576.jpg`

### Prior Study 3: 51304693
- **Date:** 2188-01-16 08:33:16
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2188-01-16_08-33-16_s51304693/`
- **Report:** `/data/patient/2188-01-16_08-33-16_s51304693/report.txt`
- **Images:** `/data/patient/2188-01-16_08-33-16_s51304693/3b8fc3bd-66391218-68c48776-0cbde359-ec4f0e4d.jpg`, `/data/patient/2188-01-16_08-33-16_s51304693/d4688d3f-0f65430c-a55e87d6-5453d43d-e5105574.jpg`

### Prior Study 4: 57289014
- **Date:** 2189-05-24 21:08:47
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2189-05-24_21-08-47_s57289014/`
- **Report:** `/data/patient/2189-05-24_21-08-47_s57289014/report.txt`
- **Images:** `/data/patient/2189-05-24_21-08-47_s57289014/505da1b4-ef3336a4-fb3f5e5e-09bb3b5e-eb1350dc.jpg`, `/data/patient/2189-05-24_21-08-47_s57289014/a30e7a85-23910be3-967d6653-109accd7-e4101dcf.jpg`

## Target Study

- **Study ID:** 56541072
- **Date:** 2190-06-04 15:02:52
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2190-06-04_15-02-52_s56541072/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2190-06-04_15-02-52_s56541072/66fece2b-2fccf418-d23f1eda-9dde45e2-d85df8da.jpg`, `/data/patient/2190-06-04_15-02-52_s56541072/f53747e0-3dd01244-eeae450a-0ae12723-4a49d191.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PA AND LAT)

**INDICATION:** History: ___M with DM1 who is presenting with elevations of blood
 sugar, vomiting and abdominal pain.

**TECHNIQUE:** Chest PA and lateral

**COMPARISON:** Chest radiograph ___, CT chest ___

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