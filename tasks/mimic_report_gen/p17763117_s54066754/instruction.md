# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17763117`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54066754`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53177649
- **Date:** 2197-02-23 13:49:40
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2197-02-23_13-49-40_s53177649/`
- **Report:** `/data/patient/2197-02-23_13-49-40_s53177649/report.txt`
- **Images:** `/data/patient/2197-02-23_13-49-40_s53177649/067df4f2-ba0ae770-919c7d21-9186536c-9c0f8174.jpg`, `/data/patient/2197-02-23_13-49-40_s53177649/9b350f75-7f987b20-092a7bbf-84be3535-8bc72c1f.jpg`

### Prior Study 2: 54899257
- **Date:** 2197-03-04 14:25:20
- **Procedure:** Performed Desc
- **Views:** LL, 
- **Folder:** `/data/patient/2197-03-04_14-25-20_s54899257/`
- **Report:** `/data/patient/2197-03-04_14-25-20_s54899257/report.txt`
- **Images:** `/data/patient/2197-03-04_14-25-20_s54899257/0c0e3903-2f744a5c-3750bad4-6d772736-6bf1c8a2.jpg`, `/data/patient/2197-03-04_14-25-20_s54899257/3e179ec6-2dd8aea9-b1ef694b-eafe6ce6-0a175813.jpg`

### Prior Study 3: 59357257
- **Date:** 2197-03-07 09:10:28
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2197-03-07_09-10-28_s59357257/`
- **Report:** `/data/patient/2197-03-07_09-10-28_s59357257/report.txt`
- **Images:** `/data/patient/2197-03-07_09-10-28_s59357257/0cfc6f6a-9b1d6469-767358c3-8cba8b86-26a9c846.jpg`, `/data/patient/2197-03-07_09-10-28_s59357257/937a086b-d6d3022b-88e3053e-885699b2-46431cc5.jpg`

### Prior Study 4: 53418217
- **Date:** 2197-04-02 01:33:18
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2197-04-02_01-33-18_s53418217/`
- **Report:** `/data/patient/2197-04-02_01-33-18_s53418217/report.txt`
- **Images:** `/data/patient/2197-04-02_01-33-18_s53418217/4c813a56-c3955f56-d8575305-9347eb08-6c581dc1.jpg`, `/data/patient/2197-04-02_01-33-18_s53418217/acddfc4f-6bf56983-900fa34f-f650d62f-a30c95af.jpg`

## Target Study

- **Study ID:** 54066754
- **Date:** 2197-04-06 05:51:20
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2197-04-06_05-51-20_s54066754/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2197-04-06_05-51-20_s54066754/2562051f-7aa8f63a-d00bafea-ddf082c6-838ba1fd.jpg`, `/data/patient/2197-04-06_05-51-20_s54066754/42721071-6d96b2ed-f083c7d3-5f14b0d5-a7845fc1.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Cough.  Right back pain.

**TECHNIQUE:** Two views of the chest.

**COMPARISON:** Multiple prior examinations, most recent radiographs dated
 ___ in correlation with CT of the chest dated ___.

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