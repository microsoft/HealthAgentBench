# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `16015751`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54907683`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54842270
- **Date:** 2172-06-03 16:01:24
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2172-06-03_16-01-24_s54842270/`
- **Report:** `/data/patient/2172-06-03_16-01-24_s54842270/report.txt`
- **Images:** `/data/patient/2172-06-03_16-01-24_s54842270/7536f4a6-1fbe0f20-f19b428c-ed5f66a2-68198980.jpg`

### Prior Study 2: 55645174
- **Date:** 2172-06-04 02:34:37
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2172-06-04_02-34-37_s55645174/`
- **Report:** `/data/patient/2172-06-04_02-34-37_s55645174/report.txt`
- **Images:** `/data/patient/2172-06-04_02-34-37_s55645174/97772d75-88b9c893-d5ad4dd5-f7763053-ca0dd70a.jpg`

### Prior Study 3: 52795401
- **Date:** 2172-06-06 12:35:14
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2172-06-06_12-35-14_s52795401/`
- **Report:** `/data/patient/2172-06-06_12-35-14_s52795401/report.txt`
- **Images:** `/data/patient/2172-06-06_12-35-14_s52795401/75420d75-4f45654a-e63a41a1-da1ad953-680cdde5.jpg`, `/data/patient/2172-06-06_12-35-14_s52795401/9b488496-6f06f792-fb185415-71bea9af-fcbd54e3.jpg`

### Prior Study 4: 57619468
- **Date:** 2172-07-12 18:13:58
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2172-07-12_18-13-58_s57619468/`
- **Report:** `/data/patient/2172-07-12_18-13-58_s57619468/report.txt`
- **Images:** `/data/patient/2172-07-12_18-13-58_s57619468/3352c0d5-7f41c92d-b1178750-7dc794c6-979ffba3.jpg`, `/data/patient/2172-07-12_18-13-58_s57619468/5c405616-b5fff6d3-129d4fb2-eec829ba-52e46d92.jpg`

## Target Study

- **Study ID:** 54907683
- **Date:** 2172-08-01 22:35:34
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, AP
- **Folder:** `/data/patient/2172-08-01_22-35-34_s54907683/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2172-08-01_22-35-34_s54907683/325742c8-9cb60d54-750e1c80-c2ee97f6-0c6d0555.jpg`, `/data/patient/2172-08-01_22-35-34_s54907683/5d18a76c-dd25b2c6-796e4972-0c023664-6bc9eff8.jpg`, `/data/patient/2172-08-01_22-35-34_s54907683/f9d601d7-0eb2306d-2e66934e-5db0f766-edb49564.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old woman with HCC, cirrhosis presenting with altered
 mental status.

**COMPARISON:** ___, CT torso ___.

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