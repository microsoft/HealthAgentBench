# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `16875792`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55853389`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 52998783
- **Date:** 2181-05-23 12:53:51
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2181-05-23_12-53-51_s52998783/`
- **Report:** `/data/patient/2181-05-23_12-53-51_s52998783/report.txt`
- **Images:** `/data/patient/2181-05-23_12-53-51_s52998783/66b2b4e8-470a1e57-77371a47-f3e6f263-0b7d1783.jpg`

### Prior Study 2: 50476602
- **Date:** 2181-06-02 12:42:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2181-06-02_12-42-18_s50476602/`
- **Report:** `/data/patient/2181-06-02_12-42-18_s50476602/report.txt`
- **Images:** `/data/patient/2181-06-02_12-42-18_s50476602/b00146a8-daf7d7b9-b5b42300-46be81dc-b7c723c0.jpg`

### Prior Study 3: 58068113
- **Date:** 2181-06-02 14:18:38
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2181-06-02_14-18-38_s58068113/`
- **Report:** `/data/patient/2181-06-02_14-18-38_s58068113/report.txt`
- **Images:** `/data/patient/2181-06-02_14-18-38_s58068113/f6eee07f-b610f72b-a8832d42-b5472b4d-7cc97271.jpg`

### Prior Study 4: 57849643
- **Date:** 2181-06-04 07:36:49
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2181-06-04_07-36-49_s57849643/`
- **Report:** `/data/patient/2181-06-04_07-36-49_s57849643/report.txt`
- **Images:** `/data/patient/2181-06-04_07-36-49_s57849643/a466a1e2-24db4349-c068db9b-aae250f4-030ceb1e.jpg`

### Prior Study 5: 58566283
- **Date:** 2181-06-04 08:48:15
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2181-06-04_08-48-15_s58566283/`
- **Report:** `/data/patient/2181-06-04_08-48-15_s58566283/report.txt`
- **Images:** `/data/patient/2181-06-04_08-48-15_s58566283/f7bbdf2d-8612cba0-b5619cfe-072a43c1-6438f2be.jpg`

### Prior Study 6: 50022945
- **Date:** 2181-06-05 17:16:13
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2181-06-05_17-16-13_s50022945/`
- **Report:** `/data/patient/2181-06-05_17-16-13_s50022945/report.txt`
- **Images:** `/data/patient/2181-06-05_17-16-13_s50022945/4331c9eb-f6e0c046-8c50bffc-6f363a16-02f0f87f.jpg`, `/data/patient/2181-06-05_17-16-13_s50022945/58e18e8d-d3328bef-ffb23510-09ee6d7a-3a0d7e9b.jpg`

## Target Study

- **Study ID:** 55853389
- **Date:** 2181-06-16 15:19:23
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2181-06-16_15-19-23_s55853389/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2181-06-16_15-19-23_s55853389/0119e0a7-198160f8-7a4b361a-0b612edd-9b62bc13.jpg`, `/data/patient/2181-06-16_15-19-23_s55853389/2c27c769-9854b0e9-102ff0b0-b17773f0-052865d7.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Evaluation of patient with persistent cough status post CABG.

**COMPARISON:** Multiple prior chest radiographs including the most recent from
 ___ along with chest CT from ___.

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