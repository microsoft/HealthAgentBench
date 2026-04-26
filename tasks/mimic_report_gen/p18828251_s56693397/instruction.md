# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `18828251`
- 6 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `56693397`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 50037292
- **Date:** 2191-11-02 19:12:30
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL, LATERAL
- **Folder:** `/data/patient/2191-11-02_19-12-30_s50037292/`
- **Report:** `/data/patient/2191-11-02_19-12-30_s50037292/report.txt`
- **Images:** `/data/patient/2191-11-02_19-12-30_s50037292/10a6246b-f2e3ec72-8c956609-ee81d40f-4a962883.jpg`, `/data/patient/2191-11-02_19-12-30_s50037292/56632a48-cce6f015-6436c85a-42883cbd-7a1c5f22.jpg`, `/data/patient/2191-11-02_19-12-30_s50037292/73a65ade-633f4da5-1c37b0a5-6a589b9c-bccae96f.jpg`

### Prior Study 2: 59257021
- **Date:** 2191-11-04 16:29:41
- **Procedure:** 
- **Views:** LL, PA
- **Folder:** `/data/patient/2191-11-04_16-29-41_s59257021/`
- **Report:** `/data/patient/2191-11-04_16-29-41_s59257021/report.txt`
- **Images:** `/data/patient/2191-11-04_16-29-41_s59257021/4e9be397-991fc87b-669cc29c-d9952817-f382bbd7.jpg`, `/data/patient/2191-11-04_16-29-41_s59257021/f608cced-6b58fb15-27c96aec-bee65e84-0155c300.jpg`

### Prior Study 3: 51246566
- **Date:** 2192-01-31 15:38:43
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2192-01-31_15-38-43_s51246566/`
- **Report:** `/data/patient/2192-01-31_15-38-43_s51246566/report.txt`
- **Images:** `/data/patient/2192-01-31_15-38-43_s51246566/fe5ade20-832e5f10-2fcedcb6-4c3c8557-e8bfb513.jpg`

### Prior Study 4: 55101327
- **Date:** 2192-05-10 14:59:56
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2192-05-10_14-59-56_s55101327/`
- **Report:** `/data/patient/2192-05-10_14-59-56_s55101327/report.txt`
- **Images:** `/data/patient/2192-05-10_14-59-56_s55101327/92fd0922-955eb1c3-1cccf867-afd0d2e5-1e5a368b.jpg`

### Prior Study 5: 56632211
- **Date:** 2192-06-22 17:15:23
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2192-06-22_17-15-23_s56632211/`
- **Report:** `/data/patient/2192-06-22_17-15-23_s56632211/report.txt`
- **Images:** `/data/patient/2192-06-22_17-15-23_s56632211/81045bbb-0ff47e0f-e6832f53-a8620841-66e813f0.jpg`, `/data/patient/2192-06-22_17-15-23_s56632211/e747e5f5-4b65dfad-f486cf2d-3b6ef7ca-50784175.jpg`

### Prior Study 6: 53348686
- **Date:** 2192-07-18 13:28:40
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2192-07-18_13-28-40_s53348686/`
- **Report:** `/data/patient/2192-07-18_13-28-40_s53348686/report.txt`
- **Images:** `/data/patient/2192-07-18_13-28-40_s53348686/35deb322-043ec12f-b33e7567-530c7a88-8b213991.jpg`, `/data/patient/2192-07-18_13-28-40_s53348686/c5c69a84-407efe78-e075f90d-1d0fe345-df3f18b3.jpg`

## Target Study

- **Study ID:** 56693397
- **Date:** 2192-09-12 14:59:21
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2192-09-12_14-59-21_s56693397/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2192-09-12_14-59-21_s56693397/7e950526-ccc5960e-735b0f76-a80365d9-139f5bff.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** Hypotensive.

**TECHNIQUE:** Semi-upright AP view of the chest.

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