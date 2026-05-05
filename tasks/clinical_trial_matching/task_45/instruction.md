# Patient-to-Trial Eligibility (Ranked)

You are working inside an environment that contains a single patient's
free-text admission note and a directory of clinical-trial documents.
**Identify every trial in the directory that the patient is eligible
for** -- meaning the patient meets all of the trial's inclusion
criteria *and* none of its exclusion criteria -- and **list them
ordered most-confident-first** (rank 1 = the trial you are most sure
the patient is eligible for).

## Inputs

- `/workspace/data/topic.txt` -- the patient case description.
- `/workspace/data/topic_id.txt` -- the integer topic ID for this task.
- `/workspace/data/trials/<NCT_ID>.xml` -- one file per candidate trial
  (typically 300-600 files). Each XML follows the standard
  ClinicalTrials.gov v1 schema with at least the following elements
  populated: `id_info/nct_id`, `brief_title`, `condition`, `intervention`,
  `eligibility/criteria/textblock`, `eligibility/gender`,
  `eligibility/minimum_age`, `eligibility/maximum_age`, and
  `brief_summary/textblock`.

## Output

Write a plain text file at
`/workspace/submission/ranked_trials.txt` containing **one NCT
identifier per line**: every trial you believe the patient is
eligible for, and **no** entries for trials where the patient is
excluded or unrelated. **The order matters** -- put the trial you
are most confident about on the first line, the next most confident
on the second, and so on. Make sure you flag all the eligible trials.

Format example (most-confident first):

    NCT00012345
    NCT00067890
    NCT00111222

Blank lines and lines starting with `#` are ignored. Duplicates are
de-duplicated keeping the first (highest-rank) occurrence.

## Rules

Solve the task using only the patient note and the trial documents in
`/workspace/data/trials/`, applying standard medical reasoning over the
patient's clinical history. Do not search the internet for benchmark
answers.
