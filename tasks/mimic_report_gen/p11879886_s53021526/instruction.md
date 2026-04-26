# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `11879886`
- 5 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `53021526`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54357764
- **Date:** 2173-10-24 01:43:58
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2173-10-24_01-43-58_s54357764/`
- **Report:** `/data/patient/2173-10-24_01-43-58_s54357764/report.txt`
- **Images:** `/data/patient/2173-10-24_01-43-58_s54357764/94795c9f-9f6f801d-ed57d02c-5e9e02be-b35bf9a1.jpg`, `/data/patient/2173-10-24_01-43-58_s54357764/9af84adc-9ec1d9e4-04c381af-f81edb77-c40f3fb4.jpg`

### Prior Study 2: 56268607
- **Date:** 2173-10-25 08:39:34
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2173-10-25_08-39-34_s56268607/`
- **Report:** `/data/patient/2173-10-25_08-39-34_s56268607/report.txt`
- **Images:** `/data/patient/2173-10-25_08-39-34_s56268607/da8cd0dd-573be530-0024ff8e-15e20b59-21e4a61d.jpg`

### Prior Study 3: 51551069
- **Date:** 2173-10-28 13:28:17
- **Procedure:** 
- **Views:** LL, PA, LL
- **Folder:** `/data/patient/2173-10-28_13-28-17_s51551069/`
- **Report:** `/data/patient/2173-10-28_13-28-17_s51551069/report.txt`
- **Images:** `/data/patient/2173-10-28_13-28-17_s51551069/1d47e5bb-33d97afb-bbb7fbb7-d59ed197-da8a12f7.jpg`, `/data/patient/2173-10-28_13-28-17_s51551069/58fedcf0-3247be4c-33428852-1d9d9fed-c613aa80.jpg`, `/data/patient/2173-10-28_13-28-17_s51551069/e1c69c1e-96a9aa50-c3ed62f9-f424f43e-99fa854d.jpg`

### Prior Study 4: 54972841
- **Date:** 2173-11-07 18:44:55
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2173-11-07_18-44-55_s54972841/`
- **Report:** `/data/patient/2173-11-07_18-44-55_s54972841/report.txt`
- **Images:** `/data/patient/2173-11-07_18-44-55_s54972841/12fcd1f0-96b6eb00-a6a5ee27-7e8d19ee-63f16bc2.jpg`, `/data/patient/2173-11-07_18-44-55_s54972841/d8d4b15b-0a338acd-c5176214-7794d508-468e6e07.jpg`

### Prior Study 5: 56855230
- **Date:** 2173-11-16 07:24:31
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2173-11-16_07-24-31_s56855230/`
- **Report:** `/data/patient/2173-11-16_07-24-31_s56855230/report.txt`
- **Images:** `/data/patient/2173-11-16_07-24-31_s56855230/2aadeb6e-8b5af4b3-f3ddd4f9-8d552d40-d8a5e821.jpg`, `/data/patient/2173-11-16_07-24-31_s56855230/a6f60ee9-d5a2f15e-67cea2a3-caf01923-79f4b71f.jpg`

## Target Study

- **Study ID:** 53021526
- **Date:** 2174-02-05 21:02:33
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2174-02-05_21-02-33_s53021526/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2174-02-05_21-02-33_s53021526/27a4f085-5eaad330-a1153870-3ec2cd19-20a604cd.jpg`, `/data/patient/2174-02-05_21-02-33_s53021526/ea6b4ed1-85a1a289-da2233a9-5ff02b4c-e6290e00.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old female with shortness of breath and history of aortic
 stenosis.  Evaluate for evidence of cardiopulmonary process.

**TECHNIQUE:** PA and lateral chest radiograph.

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