# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15446959`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `52616494`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54058678
- **Date:** 2185-02-25 02:49:22
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL
- **Folder:** `/data/patient/2185-02-25_02-49-22_s54058678/`
- **Report:** `/data/patient/2185-02-25_02-49-22_s54058678/report.txt`
- **Images:** `/data/patient/2185-02-25_02-49-22_s54058678/68adee87-49f72ff4-e7374407-bc547b35-ff118ba2.jpg`, `/data/patient/2185-02-25_02-49-22_s54058678/79efe8cb-356ec1b4-23153a48-35b3a64c-40e70a3a.jpg`

### Prior Study 2: 54692227
- **Date:** 2185-06-17 23:14:39
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP, LATERAL
- **Folder:** `/data/patient/2185-06-17_23-14-39_s54692227/`
- **Report:** `/data/patient/2185-06-17_23-14-39_s54692227/report.txt`
- **Images:** `/data/patient/2185-06-17_23-14-39_s54692227/300d9c95-b211c988-74633e84-6f6bd759-d9bd6a93.jpg`, `/data/patient/2185-06-17_23-14-39_s54692227/6bfb9064-03f991cd-bc8d36dd-fd64d740-edfaab18.jpg`, `/data/patient/2185-06-17_23-14-39_s54692227/8aac9b0d-3eb736b0-4fca393e-8604330a-916a953b.jpg`

### Prior Study 3: 51765753
- **Date:** 2186-01-10 18:10:11
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2186-01-10_18-10-11_s51765753/`
- **Report:** `/data/patient/2186-01-10_18-10-11_s51765753/report.txt`
- **Images:** `/data/patient/2186-01-10_18-10-11_s51765753/532b41c5-aa84f4e3-0680a169-3354c664-82013589.jpg`, `/data/patient/2186-01-10_18-10-11_s51765753/67521210-7de50506-706b3a67-39ab7d82-f96a75ad.jpg`

### Prior Study 4: 50714348
- **Date:** 2186-09-23 16:51:53
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2186-09-23_16-51-53_s50714348/`
- **Report:** `/data/patient/2186-09-23_16-51-53_s50714348/report.txt`
- **Images:** `/data/patient/2186-09-23_16-51-53_s50714348/01994677-4cf1e7e3-d8b77337-b9e6e43d-e2b0bf7d.jpg`, `/data/patient/2186-09-23_16-51-53_s50714348/1404cb7d-9f235a77-48962ba3-bbce9034-07178c1b.jpg`, `/data/patient/2186-09-23_16-51-53_s50714348/e5a35d58-daafa26b-836bd682-17f54c3c-a3f33527.jpg`

## Target Study

- **Study ID:** 52616494
- **Date:** 2188-01-06 21:45:25
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2188-01-06_21-45-25_s52616494/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2188-01-06_21-45-25_s52616494/647c3bd0-6e8ea0e4-e367edee-d6eefb00-174fcf42.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST RADIOGRAPH

**INDICATION:** Fever.  Question consolidation.

**TECHNIQUE:** Chest, AP semi-upright.

**COMPARISON:** ___ and ___.

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