# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14992360`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `53426027`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 50857625
- **Date:** 2191-03-23 18:53:21
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2191-03-23_18-53-21_s50857625/`
- **Report:** `/data/patient/2191-03-23_18-53-21_s50857625/report.txt`
- **Images:** `/data/patient/2191-03-23_18-53-21_s50857625/8c50fc43-5d35a129-85112298-d3630da6-c38d6a1b.jpg`, `/data/patient/2191-03-23_18-53-21_s50857625/c644ef55-2c1480c0-fa4e0e08-a92b5aa0-5b7ceb6c.jpg`

### Prior Study 2: 58503033
- **Date:** 2191-03-25 15:55:25
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2191-03-25_15-55-25_s58503033/`
- **Report:** `/data/patient/2191-03-25_15-55-25_s58503033/report.txt`
- **Images:** `/data/patient/2191-03-25_15-55-25_s58503033/32c1d55b-e82e8109-857245af-c7f729c8-050f2e67.jpg`, `/data/patient/2191-03-25_15-55-25_s58503033/d94ed77f-6e5dbc9e-c9b7dc36-fa289d86-2aed87f0.jpg`

### Prior Study 3: 50425233
- **Date:** 2192-10-02 10:51:43
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, LATERAL
- **Folder:** `/data/patient/2192-10-02_10-51-43_s50425233/`
- **Report:** `/data/patient/2192-10-02_10-51-43_s50425233/report.txt`
- **Images:** `/data/patient/2192-10-02_10-51-43_s50425233/43526336-ec395adc-91956491-ee7f2e9f-5ea5ac83.jpg`, `/data/patient/2192-10-02_10-51-43_s50425233/d131f617-7810bf73-047f6e2e-16347ff4-e18183e6.jpg`, `/data/patient/2192-10-02_10-51-43_s50425233/f95e2c77-d318c10b-c5113c5d-455b870e-eb3878e8.jpg`

### Prior Study 4: 52523882
- **Date:** 2194-02-10 18:58:25
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2194-02-10_18-58-25_s52523882/`
- **Report:** `/data/patient/2194-02-10_18-58-25_s52523882/report.txt`
- **Images:** `/data/patient/2194-02-10_18-58-25_s52523882/690e5219-a0d2190e-2017488b-4a4feda7-4ef08c2d.jpg`, `/data/patient/2194-02-10_18-58-25_s52523882/7c276a28-74265513-242b56ab-f7f75aee-b642742a.jpg`

### Prior Study 5: 52206840
- **Date:** 2194-03-09 19:41:35
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, LATERAL, PA
- **Folder:** `/data/patient/2194-03-09_19-41-35_s52206840/`
- **Report:** `/data/patient/2194-03-09_19-41-35_s52206840/report.txt`
- **Images:** `/data/patient/2194-03-09_19-41-35_s52206840/05e37d0a-c7818c2a-ac8b5b89-0daa39da-c75ec7c8.jpg`, `/data/patient/2194-03-09_19-41-35_s52206840/4ca4512c-5c8f986c-2e3448c0-1b60be7a-6946424b.jpg`, `/data/patient/2194-03-09_19-41-35_s52206840/5105ad53-1db1adf2-24a87016-dccf8db5-acfa42b3.jpg`, `/data/patient/2194-03-09_19-41-35_s52206840/9b21566f-2fa02275-f08686bc-4b67b21b-5dc922fb.jpg`

## Target Study

- **Study ID:** 53426027
- **Date:** 2194-03-12 09:10:10
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP, LATERAL
- **Folder:** `/data/patient/2194-03-12_09-10-10_s53426027/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2194-03-12_09-10-10_s53426027/2263652d-9febb548-c194ddde-3d609261-01889c9a.jpg`, `/data/patient/2194-03-12_09-10-10_s53426027/75dba8a3-5f23d588-d3d4556c-daef69cf-8ed524b4.jpg`, `/data/patient/2194-03-12_09-10-10_s53426027/9bc4f9f8-9a5cf680-f9889b51-30721129-c66aa757.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST RADIOGRAPH

**INDICATION:** History: ___M with recent fall, weakness, eval for interval change
 // eval for PNA, worsening CHF      eval for PNA, worsening CHF

**TECHNIQUE:** PA and lateral views of the chest.

**COMPARISON:** Chest radiograph from ___, chest radiograph from ___ and chest CT from ___

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