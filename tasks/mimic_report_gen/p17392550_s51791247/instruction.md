# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `17392550`
- 2 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `51791247`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 53641457
- **Date:** 2138-11-29 14:13:12
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2138-11-29_14-13-12_s53641457/`
- **Report:** `/data/patient/2138-11-29_14-13-12_s53641457/report.txt`
- **Images:** `/data/patient/2138-11-29_14-13-12_s53641457/6029ba23-5d73e768-c1fe417b-73eb330f-9c507e77.jpg`, `/data/patient/2138-11-29_14-13-12_s53641457/c08e8ebb-14a3a1f0-0da1ea4e-1b2412fb-f2d4da54.jpg`

### Prior Study 2: 57779343
- **Date:** 2138-12-26 08:06:16
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2138-12-26_08-06-16_s57779343/`
- **Report:** `/data/patient/2138-12-26_08-06-16_s57779343/report.txt`
- **Images:** `/data/patient/2138-12-26_08-06-16_s57779343/04df00d4-612ef140-93265d75-e89c65e2-d6451eb9.jpg`

## Target Study

- **Study ID:** 51791247
- **Date:** 2139-01-03 19:52:00
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, LATERAL
- **Folder:** `/data/patient/2139-01-03_19-52-00_s51791247/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2139-01-03_19-52-00_s51791247/9adf1edf-b9cd0878-60c0cc62-6a5125d2-d77223ee.jpg`, `/data/patient/2139-01-03_19-52-00_s51791247/aa0846b4-d00f5edd-d3cfefd0-2318b977-1c035245.jpg`, `/data/patient/2139-01-03_19-52-00_s51791247/b016415e-902049d0-94f8ea46-c19425cf-f3a5dfb6.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**INDICATION:** Recent hospitalizations, cough, and increasing abdominal
 distention.

**TECHNIQUE:** PA and lateral views of the chest.

**COMPARISON:** Chest CTA, ___ and chest radiograph, ___.

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