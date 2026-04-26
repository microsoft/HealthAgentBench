# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `14147380`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55599778`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54232769
- **Date:** 2167-08-30 12:00:42
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2167-08-30_12-00-42_s54232769/`
- **Report:** `/data/patient/2167-08-30_12-00-42_s54232769/report.txt`
- **Images:** `/data/patient/2167-08-30_12-00-42_s54232769/57fce1b0-808d43b3-38a72d47-a9e8bb62-3237e1a6.jpg`, `/data/patient/2167-08-30_12-00-42_s54232769/ba098029-7060e4a9-fd9101e0-40c77d8e-64caa9f2.jpg`

### Prior Study 2: 52177069
- **Date:** 2167-09-18 01:25:07
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2167-09-18_01-25-07_s52177069/`
- **Report:** `/data/patient/2167-09-18_01-25-07_s52177069/report.txt`
- **Images:** `/data/patient/2167-09-18_01-25-07_s52177069/84935982-fad67bfc-5d9710eb-129f88db-8f8c8df3.jpg`, `/data/patient/2167-09-18_01-25-07_s52177069/f6cdc51b-1af2e0c3-161713ed-feeb4791-297939fc.jpg`

### Prior Study 3: 51464763
- **Date:** 2167-10-02 02:06:15
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2167-10-02_02-06-15_s51464763/`
- **Report:** `/data/patient/2167-10-02_02-06-15_s51464763/report.txt`
- **Images:** `/data/patient/2167-10-02_02-06-15_s51464763/4c2fb727-6b6a721b-befb2d0a-f87fb73f-ee302214.jpg`, `/data/patient/2167-10-02_02-06-15_s51464763/50e94a17-5055c7d7-6d5ad603-3146fac9-dd017837.jpg`

### Prior Study 4: 57782283
- **Date:** 2167-11-13 21:08:08
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2167-11-13_21-08-08_s57782283/`
- **Report:** `/data/patient/2167-11-13_21-08-08_s57782283/report.txt`
- **Images:** `/data/patient/2167-11-13_21-08-08_s57782283/73d4997e-feb25b04-950b45f1-533d848a-d9f29409.jpg`, `/data/patient/2167-11-13_21-08-08_s57782283/778105f0-fa72bdea-8922fc0a-4d2438d9-54227b64.jpg`

## Target Study

- **Study ID:** 55599778
- **Date:** 2170-03-31 11:22:31
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, PA
- **Folder:** `/data/patient/2170-03-31_11-22-31_s55599778/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2170-03-31_11-22-31_s55599778/485dde71-5bdbc563-1574444b-95093d61-c867a5a3.jpg`, `/data/patient/2170-03-31_11-22-31_s55599778/b53a5d0c-beb58dcc-f874282d-0102846b-2e781894.jpg`, `/data/patient/2170-03-31_11-22-31_s55599778/e5c7d198-f0d2cb5b-1ad03a2c-33b67f48-db2dd55d.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PA AND LAT)

**INDICATION:** Chest and back pain 1 week after motor vehicle collision.

**TECHNIQUE:** Chest PA and lateral

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