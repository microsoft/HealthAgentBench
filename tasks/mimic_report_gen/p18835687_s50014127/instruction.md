# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `18835687`
- 7 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `50014127`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53924742
- **Date:** 2177-07-17 09:19:22
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2177-07-17_09-19-22_s53924742/`
- **Report:** `/data/patient/2177-07-17_09-19-22_s53924742/report.txt`
- **Images:** `/data/patient/2177-07-17_09-19-22_s53924742/04b94a16-2f255dc1-135c9cbd-82107f89-2d706167.jpg`

### Prior Study 2: 51719198
- **Date:** 2177-11-28 13:35:17
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, PA, LATERAL, LATERAL
- **Folder:** `/data/patient/2177-11-28_13-35-17_s51719198/`
- **Report:** `/data/patient/2177-11-28_13-35-17_s51719198/report.txt`
- **Images:** `/data/patient/2177-11-28_13-35-17_s51719198/7574674d-a958763c-1c48667a-18e60f35-dfd1f3d3.jpg`, `/data/patient/2177-11-28_13-35-17_s51719198/91bd4888-7f1222f4-5b4fe46d-db77d37b-077c6f19.jpg`, `/data/patient/2177-11-28_13-35-17_s51719198/92633e53-79ea5fb7-67adcc81-8c6f443e-7c201666.jpg`, `/data/patient/2177-11-28_13-35-17_s51719198/fbecb95d-55942985-c9904dd9-66049a82-cd83c3a2.jpg`

### Prior Study 3: 50822353
- **Date:** 2178-02-13 13:25:52
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2178-02-13_13-25-52_s50822353/`
- **Report:** `/data/patient/2178-02-13_13-25-52_s50822353/report.txt`
- **Images:** `/data/patient/2178-02-13_13-25-52_s50822353/42cb7646-ac2acc5b-504f6247-07366b48-3d2bd573.jpg`, `/data/patient/2178-02-13_13-25-52_s50822353/622257bb-496a36b2-e8d31897-1bcc260d-c1d607d2.jpg`

### Prior Study 4: 59203230
- **Date:** 2178-04-02 11:06:19
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2178-04-02_11-06-19_s59203230/`
- **Report:** `/data/patient/2178-04-02_11-06-19_s59203230/report.txt`
- **Images:** `/data/patient/2178-04-02_11-06-19_s59203230/1344069d-f5bbd6ab-956a09d4-76f8bac1-7d8c3a04.jpg`, `/data/patient/2178-04-02_11-06-19_s59203230/38e5d885-855b370d-ff1f67a4-ece45a25-cc36e325.jpg`

### Prior Study 5: 50547182
- **Date:** 2178-04-08 05:12:15
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2178-04-08_05-12-15_s50547182/`
- **Report:** `/data/patient/2178-04-08_05-12-15_s50547182/report.txt`
- **Images:** `/data/patient/2178-04-08_05-12-15_s50547182/423fc237-2b2e1394-e5255f87-97ae0a26-96fd38d9.jpg`

### Prior Study 6: 50256977
- **Date:** 2178-04-08 08:47:09
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2178-04-08_08-47-09_s50256977/`
- **Report:** `/data/patient/2178-04-08_08-47-09_s50256977/report.txt`
- **Images:** `/data/patient/2178-04-08_08-47-09_s50256977/00de6142-4e8c886c-86883a2b-ead5cc20-23399659.jpg`

### Prior Study 7: 55728799
- **Date:** 2178-04-25 16:54:33
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2178-04-25_16-54-33_s55728799/`
- **Report:** `/data/patient/2178-04-25_16-54-33_s55728799/report.txt`
- **Images:** `/data/patient/2178-04-25_16-54-33_s55728799/aa546728-20bdd90f-5ff37933-03763e88-8460fa7e.jpg`

## Target Study

- **Study ID:** 50014127
- **Date:** 2178-04-26 14:56:53
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2178-04-26_14-56-53_s50014127/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2178-04-26_14-56-53_s50014127/73da0836-553a87de-58ef0562-f9c31de6-c47927ac.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___-year-old male with HIV with shaking chills and recent
 pneumonia.  Evaluate for pneumonia.
 
 COMPARISONS:  Multiple prior chest radiographs, most recently of ___.

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