# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `10754184`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56348027`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 54594848
- **Date:** 2187-08-24 10:43:30
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2187-08-24_10-43-30_s54594848/`
- **Report:** `/data/patient/2187-08-24_10-43-30_s54594848/report.txt`
- **Images:** `/data/patient/2187-08-24_10-43-30_s54594848/36d187c2-a2f1c238-25e77d89-19d5e8b8-ca837472.jpg`, `/data/patient/2187-08-24_10-43-30_s54594848/9065147e-4fa65619-480eba86-8e159f3d-3d96acd4.jpg`

### Prior Study 2: 51837636
- **Date:** 2187-09-28 08:58:28
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2187-09-28_08-58-28_s51837636/`
- **Report:** `/data/patient/2187-09-28_08-58-28_s51837636/report.txt`
- **Images:** `/data/patient/2187-09-28_08-58-28_s51837636/2eb05c0b-30b37945-71fb6374-45cab675-82128ecc.jpg`, `/data/patient/2187-09-28_08-58-28_s51837636/47860d0e-7714c59f-fbe13df2-5e581eb8-60b60826.jpg`

### Prior Study 3: 54236662
- **Date:** 2187-12-10 09:14:36
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , 
- **Folder:** `/data/patient/2187-12-10_09-14-36_s54236662/`
- **Report:** `/data/patient/2187-12-10_09-14-36_s54236662/report.txt`
- **Images:** `/data/patient/2187-12-10_09-14-36_s54236662/17c56a39-e22f86fe-75387134-c9695d82-356794b0.jpg`, `/data/patient/2187-12-10_09-14-36_s54236662/2661a129-f2f4b642-9b833ee7-ab398d55-07a36871.jpg`

### Prior Study 4: 56625924
- **Date:** 2188-08-15 10:43:48
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2188-08-15_10-43-48_s56625924/`
- **Report:** `/data/patient/2188-08-15_10-43-48_s56625924/report.txt`
- **Images:** `/data/patient/2188-08-15_10-43-48_s56625924/526cdb3f-f4ef95d2-68e47227-531a01e7-b3f4744c.jpg`, `/data/patient/2188-08-15_10-43-48_s56625924/e12e1dd7-9b6e4d27-63a06a72-937c9716-451f2db8.jpg`

## Target Study

- **Study ID:** 56348027
- **Date:** 2190-03-29 16:56:22
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2190-03-29_16-56-22_s56348027/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2190-03-29_16-56-22_s56348027/c979aaaa-4bb31072-c9884178-6e3ced8b-edf531fa.jpg`, `/data/patient/2190-03-29_16-56-22_s56348027/e88fa460-a2901f48-730373f3-89be4f0a-89e6e2a9.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___F with pancreatic CA, afib with left flank pain after fall
 from standing  // R/O rib fracture

**TECHNIQUE:** Frontal and lateral views of the chest.

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