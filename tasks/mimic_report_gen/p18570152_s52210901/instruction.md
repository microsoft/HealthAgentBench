# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `18570152`
- 4 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `52210901`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59698565
- **Date:** 2202-03-11 18:53:28
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL, PA
- **Folder:** `/data/patient/2202-03-11_18-53-28_s59698565/`
- **Report:** `/data/patient/2202-03-11_18-53-28_s59698565/report.txt`
- **Images:** `/data/patient/2202-03-11_18-53-28_s59698565/3266c7b2-a469a79f-ec915bdc-b0101f49-8eaaf917.jpg`, `/data/patient/2202-03-11_18-53-28_s59698565/478635bb-97f592c6-a8494bc8-4ff177e8-ead686ca.jpg`, `/data/patient/2202-03-11_18-53-28_s59698565/615687f6-9c68c0c3-ea00fb31-0987abc8-6d4be9c7.jpg`

### Prior Study 2: 56605732
- **Date:** 2205-11-20 18:54:53
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, PA
- **Folder:** `/data/patient/2205-11-20_18-54-53_s56605732/`
- **Report:** `/data/patient/2205-11-20_18-54-53_s56605732/report.txt`
- **Images:** `/data/patient/2205-11-20_18-54-53_s56605732/39513708-faae323a-d74bc04a-b49a24ec-fbe051f6.jpg`, `/data/patient/2205-11-20_18-54-53_s56605732/62e28fc5-93fe9a0b-36f25627-e72bcdc7-fddf5f6e.jpg`, `/data/patient/2205-11-20_18-54-53_s56605732/a445c04c-f8447b3a-f83c989c-97f7024d-ba4c2370.jpg`

### Prior Study 3: 54399607
- **Date:** 2205-11-24 09:49:43
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2205-11-24_09-49-43_s54399607/`
- **Report:** `/data/patient/2205-11-24_09-49-43_s54399607/report.txt`
- **Images:** `/data/patient/2205-11-24_09-49-43_s54399607/68e2da8e-4b0cc570-5f6dac62-dd096bf8-ce452663.jpg`, `/data/patient/2205-11-24_09-49-43_s54399607/89a623b8-0f8a2cb9-e027aaf4-7b5828f4-9480d3a6.jpg`

### Prior Study 4: 57576479
- **Date:** 2206-07-02 14:02:32
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2206-07-02_14-02-32_s57576479/`
- **Report:** `/data/patient/2206-07-02_14-02-32_s57576479/report.txt`
- **Images:** `/data/patient/2206-07-02_14-02-32_s57576479/3aaa5c44-b88aa530-0f177d6e-7feff2d9-7d4890e2.jpg`, `/data/patient/2206-07-02_14-02-32_s57576479/bdc767d8-f9566903-2dda971f-c7110e57-164c5277.jpg`

## Target Study

- **Study ID:** 52210901
- **Date:** 2207-01-29 15:26:32
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2207-01-29_15-26-32_s52210901/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2207-01-29_15-26-32_s52210901/8328656b-7a7c59ec-fba66d3e-d4e3b7d3-2d5332bc.jpg`, `/data/patient/2207-01-29_15-26-32_s52210901/e28d8d90-6270d7bd-ea44579d-8f6861a4-2d4a40ae.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** ___ year old man with cough and fever and CLL  // r/o pneumonia

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