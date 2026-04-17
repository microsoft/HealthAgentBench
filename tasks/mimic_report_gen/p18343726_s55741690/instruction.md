# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `18343726`
- 3 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55741690`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54661616
- **Date:** 2145-02-01 17:31:17
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2145-02-01_17-31-17_s54661616/`
- **Report:** `/data/patient/2145-02-01_17-31-17_s54661616/report.txt`
- **Images:** `/data/patient/2145-02-01_17-31-17_s54661616/2bddb45e-b08f4b2d-f5594cc2-2512ff39-e6847371.jpg`, `/data/patient/2145-02-01_17-31-17_s54661616/57dd992a-c736b67a-5a1f24e1-fcef3aea-76faae84.jpg`

### Prior Study 2: 55340847
- **Date:** 2145-02-23 19:34:24
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2145-02-23_19-34-24_s55340847/`
- **Report:** `/data/patient/2145-02-23_19-34-24_s55340847/report.txt`
- **Images:** `/data/patient/2145-02-23_19-34-24_s55340847/093baa2b-62a8c5b2-9255859f-2edf2dcf-4f5ed090.jpg`, `/data/patient/2145-02-23_19-34-24_s55340847/5064b93d-bccfde44-d9c94dc5-82bb5a09-7418caa6.jpg`

### Prior Study 3: 53012323
- **Date:** 2145-07-24 16:48:54
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2145-07-24_16-48-54_s53012323/`
- **Report:** `/data/patient/2145-07-24_16-48-54_s53012323/report.txt`
- **Images:** `/data/patient/2145-07-24_16-48-54_s53012323/ceb97930-fe5ec7d6-6ee4c8aa-56e46341-d0fbfd43.jpg`, `/data/patient/2145-07-24_16-48-54_s53012323/cf70ca08-0d94fd1b-e54c0121-98ae7205-8f0f48e4.jpg`

## Target Study

- **Study ID:** 55741690
- **Date:** 2148-06-01 16:22:22
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2148-06-01_16-22-22_s55741690/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2148-06-01_16-22-22_s55741690/01ceb247-fa13bc0e-8819e99f-9df1e9e8-bba88b3d.jpg`, `/data/patient/2148-06-01_16-22-22_s55741690/2a5046e4-c023b60a-61a89d1b-464d705c-e2b1eae7.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PA AND LAT)

**INDICATION:** ___F to undergo discectomy, pre-op film

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