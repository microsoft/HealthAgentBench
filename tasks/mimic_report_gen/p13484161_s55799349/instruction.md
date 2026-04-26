# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `13484161`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55799349`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54526081
- **Date:** 2177-10-03 09:22:52
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2177-10-03_09-22-52_s54526081/`
- **Report:** `/data/patient/2177-10-03_09-22-52_s54526081/report.txt`
- **Images:** `/data/patient/2177-10-03_09-22-52_s54526081/95906129-89721086-cc8154fa-07c91f7e-3c5ea511.jpg`

### Prior Study 2: 56546504
- **Date:** 2177-10-16 11:46:20
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2177-10-16_11-46-20_s56546504/`
- **Report:** `/data/patient/2177-10-16_11-46-20_s56546504/report.txt`
- **Images:** `/data/patient/2177-10-16_11-46-20_s56546504/1d7ab682-be7aac39-ca9dd307-1d094e9c-b2f306d6.jpg`, `/data/patient/2177-10-16_11-46-20_s56546504/c771fda7-294984e2-40d6b8b3-eeec5c1c-95760ad3.jpg`

### Prior Study 3: 51009376
- **Date:** 2177-10-16 08:37:33
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2177-10-16_08-37-33_s51009376/`
- **Report:** `/data/patient/2177-10-16_08-37-33_s51009376/report.txt`
- **Images:** `/data/patient/2177-10-16_08-37-33_s51009376/e120ed69-a974706b-30acf181-38be212f-48eb872d.jpg`

### Prior Study 4: 55812727
- **Date:** 2178-10-16 14:16:35
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2178-10-16_14-16-35_s55812727/`
- **Report:** `/data/patient/2178-10-16_14-16-35_s55812727/report.txt`
- **Images:** `/data/patient/2178-10-16_14-16-35_s55812727/0f3b10cd-b3e6a500-20370ada-6e3ab8b3-ad1019c5.jpg`, `/data/patient/2178-10-16_14-16-35_s55812727/42c8ec81-8a76040b-dacb834e-034b24d0-da9eedbe.jpg`

## Target Study

- **Study ID:** 55799349
- **Date:** 2179-09-11 21:06:51
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2179-09-11_21-06-51_s55799349/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2179-09-11_21-06-51_s55799349/08614ec0-0b852187-5ffa5362-16e023b7-1366cc0f.jpg`, `/data/patient/2179-09-11_21-06-51_s55799349/d45a4f1c-aa9b0b1d-714e476e-b6f28f01-34d6bcdc.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

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