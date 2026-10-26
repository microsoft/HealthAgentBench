# Radiology Report Correction

A draft radiology report for this patient's most recent chest X-ray
study has been prepared by a junior radiologist. The draft is already
populated in the `FINDINGS:` section of the target study's `report.txt`
under `/data/patient/<target_study>/`. The draft might contain
clinical errors — your job is to **review and correct it**.

Use the chest-X-ray images and the prior reports (if any) to determine
the correct findings.

**Correction rules:**

1. You may **edit** existing sentences in the draft (reword them, fix
   the described finding, or remove a sentence that is wrong).
2. You **may not add** new statements about findings the draft did not
   already mention. The draft should already address every relevant
   finding.
3. Submit only the corrected FINDINGS section. No IMPRESSION is
   expected and it is not scored.

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
  `study_NN`) is the TARGET study.
- **Prior** studies' `report.txt` contains the full original report
  (FINDINGS + IMPRESSION + everything else).
- The **target** study's `report.txt` contains the non-generated
  sections (EXAMINATION, INDICATION, HISTORY, TECHNIQUE, COMPARISON)
  followed by a `FINDINGS:` section with the **draft to be corrected**.

## Your output

`/workspace/submission.json` already exists and contains a JSON list
with a single entry:

```json
[
  {
    "task_id": "<pre-filled>",
    "final_answer": ""
  }
]
```

- Set **only** the `final_answer` field to the corrected report.
- **Do not modify `task_id`**, and do not add, remove, or rename any
  other entries or keys. The file must remain a JSON list with this
  one object.
- `final_answer` must **start with the literal `FINDINGS:` header on
  its own line, followed by your corrected body text.** Do not include
  an IMPRESSION section — only FINDINGS is scored.

Example `final_answer` value:

```
FINDINGS:
The lungs are hyperinflated... [your corrected text]
```

Update `submission.json` with a JSON-aware tool such as Python
(e.g. `python -c "import json; ..."`); manual string edits easily
corrupt the JSON.

## Resources

You have 1 hour to complete the task. There is no internet access beyond the model
API. The container is configured for 2 CPUs, 4 GiB of memory, 10 GiB of disk, and no
GPU. System tools may report host resources, not these limits.
