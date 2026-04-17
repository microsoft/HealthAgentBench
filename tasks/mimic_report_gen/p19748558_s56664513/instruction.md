# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `19748558`
- 7 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56664513`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59372049
- **Date:** 2164-01-12 14:34:03
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2164-01-12_14-34-03_s59372049/`
- **Report:** `/data/patient/2164-01-12_14-34-03_s59372049/report.txt`
- **Images:** `/data/patient/2164-01-12_14-34-03_s59372049/8b08f860-baa48664-53adfb7a-98469602-de45d5e7.jpg`, `/data/patient/2164-01-12_14-34-03_s59372049/baf21f49-b3c34e24-016e1cf0-2d79e385-87cef256.jpg`

### Prior Study 2: 59041431
- **Date:** 2164-06-12 09:24:53
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2164-06-12_09-24-53_s59041431/`
- **Report:** `/data/patient/2164-06-12_09-24-53_s59041431/report.txt`
- **Images:** `/data/patient/2164-06-12_09-24-53_s59041431/30bc9b40-a8f3abb2-ed8a5db2-ec23cd7f-21ea4f1f.jpg`, `/data/patient/2164-06-12_09-24-53_s59041431/9905499f-c48f304d-f9efd154-a921881b-f71b7f86.jpg`

### Prior Study 3: 51391219
- **Date:** 2164-08-14 08:02:55
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2164-08-14_08-02-55_s51391219/`
- **Report:** `/data/patient/2164-08-14_08-02-55_s51391219/report.txt`
- **Images:** `/data/patient/2164-08-14_08-02-55_s51391219/ac638c9f-e5d8c3ae-fe914812-72a8fa82-e38477e7.jpg`, `/data/patient/2164-08-14_08-02-55_s51391219/e585ac0f-fc079ecc-ae54b1f8-1121c4b0-52a0b7f0.jpg`

### Prior Study 4: 53711569
- **Date:** 2165-02-19 08:11:51
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, AP
- **Folder:** `/data/patient/2165-02-19_08-11-51_s53711569/`
- **Report:** `/data/patient/2165-02-19_08-11-51_s53711569/report.txt`
- **Images:** `/data/patient/2165-02-19_08-11-51_s53711569/bb607dbd-ec5d6d2b-1f3eba1f-9026a26b-d4e9cf3a.jpg`, `/data/patient/2165-02-19_08-11-51_s53711569/de4ee2bc-3ef01fba-d43e28af-4a6cf54a-3097a054.jpg`, `/data/patient/2165-02-19_08-11-51_s53711569/e340b826-77b272b0-563eb16a-9d61d7c8-debd50bf.jpg`

### Prior Study 5: 54913354
- **Date:** 2166-02-16 23:30:24
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2166-02-16_23-30-24_s54913354/`
- **Report:** `/data/patient/2166-02-16_23-30-24_s54913354/report.txt`
- **Images:** `/data/patient/2166-02-16_23-30-24_s54913354/7ee153a9-e00f7cd0-8c44b852-d83a1175-db28c1e7.jpg`, `/data/patient/2166-02-16_23-30-24_s54913354/887d2084-05ef3dd9-2c675409-df755081-60950f2a.jpg`

### Prior Study 6: 51371355
- **Date:** 2166-10-17 18:15:21
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2166-10-17_18-15-21_s51371355/`
- **Report:** `/data/patient/2166-10-17_18-15-21_s51371355/report.txt`
- **Images:** `/data/patient/2166-10-17_18-15-21_s51371355/de6f3d70-eadfcea2-4074743a-28118cf6-707e9cfd.jpg`

### Prior Study 7: 53919021
- **Date:** 2167-02-20 19:29:19
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2167-02-20_19-29-19_s53919021/`
- **Report:** `/data/patient/2167-02-20_19-29-19_s53919021/report.txt`
- **Images:** `/data/patient/2167-02-20_19-29-19_s53919021/59a9547b-1d1ae94d-21f9b870-53488792-48240baa.jpg`, `/data/patient/2167-02-20_19-29-19_s53919021/6eaf56a0-ded30052-29edb3ad-20da2133-db0cf728.jpg`

## Target Study

- **Study ID:** 56664513
- **Date:** 2167-05-01 08:12:36
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2167-05-01_08-12-36_s56664513/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2167-05-01_08-12-36_s56664513/f6996351-b7330fe0-c77b11b0-628b7301-475c940f.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** CHEST (PORTABLE AP)

**INDICATION:** ___ year old man with hypoxia, leukocytosis, and AMS.  // Please
 eval for e/o pneumonia or aspiration.

**TECHNIQUE:** Single AP view of the chest

**COMPARISON:** Multiple chest radiographs the most recent on ___

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