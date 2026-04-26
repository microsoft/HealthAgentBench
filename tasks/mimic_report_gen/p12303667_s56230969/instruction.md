# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `12303667`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56230969`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53999109
- **Date:** 2171-09-13 17:26:04
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2171-09-13_17-26-04_s53999109/`
- **Report:** `/data/patient/2171-09-13_17-26-04_s53999109/report.txt`
- **Images:** `/data/patient/2171-09-13_17-26-04_s53999109/ba5d48f0-3105c3a1-1e049eec-c72ac120-415942b0.jpg`

### Prior Study 2: 52329768
- **Date:** 2171-09-25 16:32:02
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2171-09-25_16-32-02_s52329768/`
- **Report:** `/data/patient/2171-09-25_16-32-02_s52329768/report.txt`
- **Images:** `/data/patient/2171-09-25_16-32-02_s52329768/279895b7-16a23c5e-1aea2909-baa62b3f-884b6f9e.jpg`, `/data/patient/2171-09-25_16-32-02_s52329768/ab5d8429-a48d1b05-af73d020-ef1f6e53-30f8ae8d.jpg`

### Prior Study 3: 51202805
- **Date:** 2172-04-15 21:17:57
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2172-04-15_21-17-57_s51202805/`
- **Report:** `/data/patient/2172-04-15_21-17-57_s51202805/report.txt`
- **Images:** `/data/patient/2172-04-15_21-17-57_s51202805/8c86917f-0d8be3f4-f464a18e-3638f3a1-343d29c4.jpg`, `/data/patient/2172-04-15_21-17-57_s51202805/f13c668b-a7cbd8c4-3de552f9-4c0921fe-7c8b4a12.jpg`

### Prior Study 4: 58981887
- **Date:** 2172-05-02 16:04:44
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2172-05-02_16-04-44_s58981887/`
- **Report:** `/data/patient/2172-05-02_16-04-44_s58981887/report.txt`
- **Images:** `/data/patient/2172-05-02_16-04-44_s58981887/b1eb70c2-97d846e5-476dfd4b-52ab781f-bcbbb7a2.jpg`, `/data/patient/2172-05-02_16-04-44_s58981887/be82eebb-cd25c088-b3c1ddfa-6ccf0b10-880a3a77.jpg`

### Prior Study 5: 56901171
- **Date:** 2172-05-14 08:51:09
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2172-05-14_08-51-09_s56901171/`
- **Report:** `/data/patient/2172-05-14_08-51-09_s56901171/report.txt`
- **Images:** `/data/patient/2172-05-14_08-51-09_s56901171/8be5e566-84d421c6-72d46c14-79091c67-73751f9f.jpg`

### Prior Study 6: 54218896
- **Date:** 2173-04-02 22:36:15
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2173-04-02_22-36-15_s54218896/`
- **Report:** `/data/patient/2173-04-02_22-36-15_s54218896/report.txt`
- **Images:** `/data/patient/2173-04-02_22-36-15_s54218896/e4e0e4ff-71138eac-7cef38bd-ce820887-d59037ff.jpg`

## Target Study

- **Study ID:** 56230969
- **Date:** 2174-02-03 11:31:54
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2174-02-03_11-31-54_s56230969/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2174-02-03_11-31-54_s56230969/9ed98f0d-44106851-df647480-672d93ed-95426753.jpg`, `/data/patient/2174-02-03_11-31-54_s56230969/b8ec370f-450e80d9-25461f27-72d3da41-d6e10bae.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** Lymphangioleimyomatosis with cough fevers and wheezing for 1 month,
 evaluate for pneumonia.

**COMPARISON:** Chest radiographs from ___ and ___.

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