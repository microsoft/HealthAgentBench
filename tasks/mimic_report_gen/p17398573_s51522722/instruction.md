# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17398573`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51522722`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 50918803
- **Date:** 2183-01-12 11:02:44
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2183-01-12_11-02-44_s50918803/`
- **Report:** `/data/patient/2183-01-12_11-02-44_s50918803/report.txt`
- **Images:** `/data/patient/2183-01-12_11-02-44_s50918803/31c1ff27-efe0b34c-f8b81088-73df6e0c-836198d5.jpg`, `/data/patient/2183-01-12_11-02-44_s50918803/809123a3-3a8ec764-0d6f069f-d1b0935b-161bfff4.jpg`

### Prior Study 2: 53325824
- **Date:** 2183-02-03 19:33:48
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2183-02-03_19-33-48_s53325824/`
- **Report:** `/data/patient/2183-02-03_19-33-48_s53325824/report.txt`
- **Images:** `/data/patient/2183-02-03_19-33-48_s53325824/06381bf5-e227679d-9f9965ef-dbbb229c-281230a2.jpg`, `/data/patient/2183-02-03_19-33-48_s53325824/6a31f7f3-592b6144-a0b7e38c-d11761b4-bd2bf9e3.jpg`

### Prior Study 3: 51909919
- **Date:** 2187-05-23 18:46:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2187-05-23_18-46-18_s51909919/`
- **Report:** `/data/patient/2187-05-23_18-46-18_s51909919/report.txt`
- **Images:** `/data/patient/2187-05-23_18-46-18_s51909919/cc9633ee-0f1c87c6-d3eab33a-ac1eccd5-1bd7608f.jpg`

### Prior Study 4: 52640725
- **Date:** 2187-05-23 21:15:28
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2187-05-23_21-15-28_s52640725/`
- **Report:** `/data/patient/2187-05-23_21-15-28_s52640725/report.txt`
- **Images:** `/data/patient/2187-05-23_21-15-28_s52640725/6722c21a-9a65dc03-dbc8707e-83f326f7-09e1768c.jpg`

## Target Study

- **Study ID:** 51522722
- **Date:** 2187-11-21 01:21:25
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2187-11-21_01-21-25_s51522722/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2187-11-21_01-21-25_s51522722/4a102c0d-0f7d000d-98e8aac0-7509e4c8-b9d60545.jpg`, `/data/patient/2187-11-21_01-21-25_s51522722/f9ce0a6c-67455c98-67d8a2c9-c6e73fd9-9753b4aa.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** Chest:  Frontal and lateral views

**INDICATION:** History: ___F with leukocytosis  // eval for pna

**TECHNIQUE:** Chest:  Frontal and Lateral

**COMPARISON:** Chest radiograph on ___

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