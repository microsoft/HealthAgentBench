# Radiology Report Generation

Generate the **FINDINGS** and **IMPRESSION** sections of a radiology
report for this patient's most recent chest X-ray study. Both
sections are required; the verifier compares the FINDINGS against
the reference for clinical errors (CheXprompt), and IMPRESSION is
expected as a clinically complete report.

**You have up to 1 hour to complete this task.** Plan your
exploration of the patient folder accordingly and write your
FINDINGS + IMPRESSION well before the deadline.

## Workspace layout

All data under `/data/patient/` belongs to a **single patient**.
Each subfolder is one chest-X-ray study for that patient:

```
/data/patient/
    study_01_2150-03-15_14-30-22/
        view_01.jpg             # one or more chest X-ray views
        view_02.jpg
        report.txt              # see below
    study_02_2150-03-29_09-12-08/
        view_01.jpg
        ...
```

- Folder names follow the pattern ``study_NN_YYYY-MM-DD_HH-MM-SS``,
  where the suffix is the study's actual timestamp. They sort
  chronologically. The **last** folder (highest-numbered
  ``study_NN``) is the TARGET study (the one to write FINDINGS +
  IMPRESSION for).
- For **prior** studies, `report.txt` is the *full* radiology
  report (all sections including findings and impression). Use
  them to understand the patient's history.
- For the **target** study, `report.txt` contains every section
  except FINDINGS and IMPRESSION — typically EXAMINATION,
  INDICATION, HISTORY, TECHNIQUE, COMPARISON. Read it for the
  clinical question being asked.

## Your output

Set `final_answer` in `/workspace/submission.json` to FINDINGS
and IMPRESSION text formatted exactly as:

```
FINDINGS:
<your findings text>

IMPRESSION:
<your impression text>
```

Do NOT include EXAMINATION/INDICATION/TECHNIQUE/COMPARISON/HISTORY
headers in your answer — those are already in the report.

You should not cheat and you should not directly retrieve answers from internet.

Use a JSON-aware tool to edit `submission.json` (e.g. `python -c
"import json; ..."`); manual string edits easily corrupt the JSON.
