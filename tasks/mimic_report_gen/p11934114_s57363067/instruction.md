# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `11934114`
- 11 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `57363067`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 55027268
- **Date:** 2136-04-07 11:29:54
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-07_11-29-54_s55027268/`
- **Report:** `/data/patient/2136-04-07_11-29-54_s55027268/report.txt`
- **Images:** `/data/patient/2136-04-07_11-29-54_s55027268/e32d8967-9d4234f1-98ac9b11-3c5e73f4-cc690e1a.jpg`

### Prior Study 2: 51328698
- **Date:** 2136-04-07 12:19:57
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-07_12-19-57_s51328698/`
- **Report:** `/data/patient/2136-04-07_12-19-57_s51328698/report.txt`
- **Images:** `/data/patient/2136-04-07_12-19-57_s51328698/f9a68aca-c5a51654-80b6c990-e35e78ae-63dcc3b2.jpg`

### Prior Study 3: 53100359
- **Date:** 2136-04-08 04:19:38
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-08_04-19-38_s53100359/`
- **Report:** `/data/patient/2136-04-08_04-19-38_s53100359/report.txt`
- **Images:** `/data/patient/2136-04-08_04-19-38_s53100359/dc63738e-e751f65e-82a68318-2d812b04-d30cf7f3.jpg`

### Prior Study 4: 52020944
- **Date:** 2136-04-09 16:38:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-09_16-38-06_s52020944/`
- **Report:** `/data/patient/2136-04-09_16-38-06_s52020944/report.txt`
- **Images:** `/data/patient/2136-04-09_16-38-06_s52020944/df76c29b-3a305594-6510b7d9-7054ad7c-fb7278a0.jpg`

### Prior Study 5: 59763671
- **Date:** 2136-04-10 08:16:38
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-10_08-16-38_s59763671/`
- **Report:** `/data/patient/2136-04-10_08-16-38_s59763671/report.txt`
- **Images:** `/data/patient/2136-04-10_08-16-38_s59763671/91c320f3-73212556-e2380f4b-f3331485-e35cf39e.jpg`

### Prior Study 6: 52152296
- **Date:** 2136-04-18 11:03:40
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-18_11-03-40_s52152296/`
- **Report:** `/data/patient/2136-04-18_11-03-40_s52152296/report.txt`
- **Images:** `/data/patient/2136-04-18_11-03-40_s52152296/67653b61-d4cdc144-670c5d2f-1d19f3a2-480d85a1.jpg`

### Prior Study 7: 50921864
- **Date:** 2136-04-18 14:35:02
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-18_14-35-02_s50921864/`
- **Report:** `/data/patient/2136-04-18_14-35-02_s50921864/report.txt`
- **Images:** `/data/patient/2136-04-18_14-35-02_s50921864/07b49600-045da45b-0a9a9c85-40312bf9-29eb90ba.jpg`

### Prior Study 8: 58725099
- **Date:** 2136-04-18 16:17:49
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-18_16-17-49_s58725099/`
- **Report:** `/data/patient/2136-04-18_16-17-49_s58725099/report.txt`
- **Images:** `/data/patient/2136-04-18_16-17-49_s58725099/f1a86b6c-1907b6f9-4893b125-c7f89eee-604fbd73.jpg`

### Prior Study 9: 51139077
- **Date:** 2136-04-22 12:36:13
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-22_12-36-13_s51139077/`
- **Report:** `/data/patient/2136-04-22_12-36-13_s51139077/report.txt`
- **Images:** `/data/patient/2136-04-22_12-36-13_s51139077/4fc6f280-2eae00ca-b8720682-3d0a8eee-b2dbb3c6.jpg`

### Prior Study 10: 58600769
- **Date:** 2136-04-25 10:50:36
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2136-04-25_10-50-36_s58600769/`
- **Report:** `/data/patient/2136-04-25_10-50-36_s58600769/report.txt`
- **Images:** `/data/patient/2136-04-25_10-50-36_s58600769/60fa6a80-205ed57c-835e6296-1969c8b7-58eeaacf.jpg`

### Prior Study 11: 52625540
- **Date:** 2136-04-27 13:36:25
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2136-04-27_13-36-25_s52625540/`
- **Report:** `/data/patient/2136-04-27_13-36-25_s52625540/report.txt`
- **Images:** `/data/patient/2136-04-27_13-36-25_s52625540/de3aab87-d8c3b45e-2312deb9-70e80ce0-17b557d2.jpg`, `/data/patient/2136-04-27_13-36-25_s52625540/fee52ef3-e8e58680-e83b3d50-fa52077b-106381ff.jpg`

## Target Study

- **Study ID:** 57363067
- **Date:** 2136-05-05 08:28:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2136-05-05_08-28-06_s57363067/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2136-05-05_08-28-06_s57363067/14f914fe-fe271488-782a6d68-11bd9c45-8c2b816b.jpg`, `/data/patient/2136-05-05_08-28-06_s57363067/d8bc7ccc-a2bac7c8-1dd6d0a5-5ed27c66-4f556bac.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**EXAMINATION:** Multiple frontal chest radiographs.
 
 COMPARISONS:  ___ and ___.

**INDICATION:** ___-year-old female with urosepsis and respiratory distress with
 new oxygen requirement.  Evaluate for acute prior cardiopulmonary process.

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