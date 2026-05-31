# Radiology Report Correction

A draft radiology report for this patient's most recent chest X-ray
study has been prepared by a junior radiologist. The draft is already
populated in the `FINDINGS:` section of the target study's `report.txt`
under `/data/patient/<target_study>/`. The draft might contain
clinical errors — your job is to **review and correct it**.

**Rules:**

1. You may **edit** existing sentences in the draft.
2. The draft should already address the relevant findings — you **may not add** new statements about findings the draft did not
   already mention. 
3. Submit only the corrected FINDINGS section. No IMPRESSION is
   expected.

Use the chest-X-ray images and the prior reports (if any) to determine
the correct findings.

**You have up to 1 hour to complete this task.**

## Workspace layout

All data under `/data/patient/` belongs to a **single patient**. Each
subfolder is one chest-X-ray study for that patient:

```
/data/patient/
    study_01_<timestamp>/
        view_01.jpg
        view_02.jpg
        report.txt          # prior: full report INCLUDING FINDINGS+IMPRESSION
    study_02_<timestamp>/
        ...
    study_NN_<timestamp>/   # TARGET (highest-numbered)
        view_01.jpg
        report.txt          # has EXAMINATION/INDICATION/HISTORY/...
                            # and a DRAFT FINDINGS section to correct
```

- Folder names sort chronologically. The **last** folder (highest
  ``study_NN``) is the TARGET study.
- **Prior** studies' `report.txt` contains the full original report
  (FINDINGS + IMPRESSION + everything else).
- The **target** study's `report.txt` contains the non-generated
  sections (EXAMINATION, INDICATION, HISTORY, TECHNIQUE, COMPARISON)
  followed by a `FINDINGS:` section with the **draft to be corrected**.

## Your output

Set `final_answer` in `/workspace/submission.json` to the corrected
report. **Start with the literal `FINDINGS:` header on its own line,
followed by your corrected body text.** Do not include an IMPRESSION
section — only FINDINGS is scored.

Example:

```
FINDINGS:
The lungs are hyperinflated... [your corrected text]
```

Use a JSON-aware tool to edit `submission.json` (e.g. `python -c "import
json; ..."`); manual string edits easily corrupt the JSON.

You should not cheat and you should not directly look up the end
solutions from the internet.
