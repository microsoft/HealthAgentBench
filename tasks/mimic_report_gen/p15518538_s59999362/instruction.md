# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15518538`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `59999362`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 50194541
- **Date:** 2126-07-14 15:39:03
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2126-07-14_15-39-03_s50194541/`
- **Report:** `/data/patient/2126-07-14_15-39-03_s50194541/report.txt`
- **Images:** `/data/patient/2126-07-14_15-39-03_s50194541/88f5aab2-59d65dc0-384b49ce-d7a62771-3c098482.jpg`

### Prior Study 2: 55758533
- **Date:** 2126-11-28 13:03:45
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, PA, LATERAL
- **Folder:** `/data/patient/2126-11-28_13-03-45_s55758533/`
- **Report:** `/data/patient/2126-11-28_13-03-45_s55758533/report.txt`
- **Images:** `/data/patient/2126-11-28_13-03-45_s55758533/41f318a8-7cfeafa3-86187822-84d18ca4-153b1ecf.jpg`, `/data/patient/2126-11-28_13-03-45_s55758533/44fd9408-57bb7612-99f6002c-71e76b77-a2040d14.jpg`, `/data/patient/2126-11-28_13-03-45_s55758533/503c3e2e-fdb4d0be-816c24b3-5fd7d8cf-d0f61456.jpg`

### Prior Study 3: 53078789
- **Date:** 2129-01-29 12:57:06
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2129-01-29_12-57-06_s53078789/`
- **Report:** `/data/patient/2129-01-29_12-57-06_s53078789/report.txt`
- **Images:** `/data/patient/2129-01-29_12-57-06_s53078789/0c5f56c2-3d707105-b36af285-88d0ae60-48ef3fda.jpg`, `/data/patient/2129-01-29_12-57-06_s53078789/d18abe57-80923646-8d3f05f6-dafedd8b-289ed541.jpg`

### Prior Study 4: 59504476
- **Date:** 2129-02-27 12:18:45
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2129-02-27_12-18-45_s59504476/`
- **Report:** `/data/patient/2129-02-27_12-18-45_s59504476/report.txt`
- **Images:** `/data/patient/2129-02-27_12-18-45_s59504476/70ad5a5e-35834f2a-a5619c1e-5deaac58-b6657063.jpg`, `/data/patient/2129-02-27_12-18-45_s59504476/c3fe2619-5e9d2145-d9f7ccdc-a0bafc7b-6cf0c98d.jpg`

## Target Study

- **Study ID:** 59999362
- **Date:** 2129-06-12 14:10:20
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2129-06-12_14-10-20_s59999362/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2129-06-12_14-10-20_s59999362/f1096194-814152f3-c5c14405-305b19d8-0d4eaffb.jpg`, `/data/patient/2129-06-12_14-10-20_s59999362/fb713bef-44a802dc-179def5b-4baaedb7-991610c2.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** Chest:  Frontal and lateral views

**INDICATION:** History: ___M with c/o CP  // ? PNA

**TECHNIQUE:** Chest Frontal and Lateral

**COMPARISON:** ___

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