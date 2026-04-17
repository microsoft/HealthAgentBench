# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `19549821`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56042734`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 56573421
- **Date:** 2116-07-30 14:31:07
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2116-07-30_14-31-07_s56573421/`
- **Report:** `/data/patient/2116-07-30_14-31-07_s56573421/report.txt`
- **Images:** `/data/patient/2116-07-30_14-31-07_s56573421/35ba5821-6f988e43-c7ce7779-9947c2dc-064358ad.jpg`, `/data/patient/2116-07-30_14-31-07_s56573421/bc763820-6af428a2-67311ece-8d067825-f6282dba.jpg`

### Prior Study 2: 59966980
- **Date:** 2117-08-19 16:24:01
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2117-08-19_16-24-01_s59966980/`
- **Report:** `/data/patient/2117-08-19_16-24-01_s59966980/report.txt`
- **Images:** `/data/patient/2117-08-19_16-24-01_s59966980/c810fda6-49f22def-580efb22-d9ed1837-c3e002b1.jpg`

### Prior Study 3: 55593187
- **Date:** 2117-09-05 18:22:41
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2117-09-05_18-22-41_s55593187/`
- **Report:** `/data/patient/2117-09-05_18-22-41_s55593187/report.txt`
- **Images:** `/data/patient/2117-09-05_18-22-41_s55593187/318e2d2a-cd564b66-987b939f-2b0ded80-8fc82ad2.jpg`, `/data/patient/2117-09-05_18-22-41_s55593187/b3e3cd04-672dd424-cb6d9ca6-59bdd243-0fa75b80.jpg`

### Prior Study 4: 59953900
- **Date:** 2117-09-07 04:46:43
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2117-09-07_04-46-43_s59953900/`
- **Report:** `/data/patient/2117-09-07_04-46-43_s59953900/report.txt`
- **Images:** `/data/patient/2117-09-07_04-46-43_s59953900/a6af277c-9bba350e-4a71b3e8-137d82db-cb01dd0e.jpg`

### Prior Study 5: 54696287
- **Date:** 2117-09-08 10:12:56
- **Procedure:** Performed Desc
- **Views:** PA, LL, LL
- **Folder:** `/data/patient/2117-09-08_10-12-56_s54696287/`
- **Report:** `/data/patient/2117-09-08_10-12-56_s54696287/report.txt`
- **Images:** `/data/patient/2117-09-08_10-12-56_s54696287/9a4ccf98-58c3f0da-81d2cd90-38c242fb-cc48af1b.jpg`, `/data/patient/2117-09-08_10-12-56_s54696287/bdd5a7d2-2ce12b6b-b5e7b44e-b9332707-80c08524.jpg`, `/data/patient/2117-09-08_10-12-56_s54696287/f10aba88-cfb8f760-c3b288f6-c1d76c27-88bfb3e0.jpg`

### Prior Study 6: 56024784
- **Date:** 2117-10-11 09:37:26
- **Procedure:** Performed Desc
- **Views:** LL, , LL
- **Folder:** `/data/patient/2117-10-11_09-37-26_s56024784/`
- **Report:** `/data/patient/2117-10-11_09-37-26_s56024784/report.txt`
- **Images:** `/data/patient/2117-10-11_09-37-26_s56024784/3db433a8-9379d041-b4e9d173-f253fe8b-8ad21d0a.jpg`, `/data/patient/2117-10-11_09-37-26_s56024784/41cf21eb-9d52be87-edeedec8-7aecd1ac-5e5662c4.jpg`, `/data/patient/2117-10-11_09-37-26_s56024784/4bb967c3-58f8c025-777fd624-8d104e92-18a9526a.jpg`

## Target Study

- **Study ID:** 56042734
- **Date:** 2118-06-09 14:18:57
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, LATERAL, PA
- **Folder:** `/data/patient/2118-06-09_14-18-57_s56042734/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2118-06-09_14-18-57_s56042734/7377346a-38f8250e-c3694853-37601fdd-b0ff4cb7.jpg`, `/data/patient/2118-06-09_14-18-57_s56042734/a464fe33-f97c23c1-580d2988-155f758e-66524a5f.jpg`, `/data/patient/2118-06-09_14-18-57_s56042734/c7c68b52-54b2bc92-e88ecc8c-e4048535-e3dbb409.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** ___-year-old female with hyperglycemia.  Evaluation for pneumonia.

**COMPARISON:** Comparison is made to radiographs of the chest from ___.

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