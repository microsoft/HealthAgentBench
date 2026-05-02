# Patient-to-Trial Matching

You are working inside an environment that contains a single patient's
free-text admission note and a directory of clinical-trial documents.
Rank the trials by how well the patient matches them, favoring trials the
patient would be eligible to enroll in.

## Inputs

- `/workspace/data/topic.txt` -- the patient case description.
- `/workspace/data/topic_id.txt` -- the integer topic ID you must use in
  the `TOPIC_NO` column of your submission.
- `/workspace/data/trials/<NCT_ID>.xml` -- one file per candidate trial
  (typically 300-600 files). Each XML follows the standard
  ClinicalTrials.gov v1 schema with at least the following elements
  populated: `id_info/nct_id`, `brief_title`, `condition`, `intervention`,
  `eligibility/criteria/textblock`, `eligibility/gender`,
  `eligibility/minimum_age`, `eligibility/maximum_age`, and
  `brief_summary/textblock`.

## Output

Write a run file at `/workspace/submission/run.txt` in standard
ad-hoc-retrieval format. Each line must have six whitespace-separated
fields:

    TOPIC_NO Q0 NCT_ID RANK SCORE RUN_NAME

Where:

- `TOPIC_NO` matches `topic_id.txt`.
- `Q0` is a literal placeholder.
- `NCT_ID` is one of the candidate trials (a filename under
  `/workspace/data/trials/` without the `.xml` suffix).
- `RANK` is a 1-based integer; same-score ties get distinct ranks.
- `SCORE` is a floating-point value, larger = more confident match.
- `RUN_NAME` is any short alphanumeric label without spaces.

Submit **your top 10 trials** (the 10 you are most confident match the
patient), sorted by rank ascending. Only the top-10 ranks contribute to
the score; submitting more than 10 rows is permitted but they will not
affect your reward, so prioritize getting the top 10 right.

## Scoring

The verifier scores your ranking using NDCG@10 (Normalized Discounted
Cumulative Gain at cutoff 10) with graded relevance:

- `eligible` (highest credit)
- `excluded` (partial credit -- patient meets inclusion criteria but is
  excluded by an exclusion criterion)
- `not relevant` (no credit)

NDCG rewards placing relevant trials at the top of the list; placing
trials far down the list contributes little. NDCG@10 is in [0, 1].

## Rules

Solve the task using only the patient note and the trial documents in
`/workspace/data/trials/`, applying standard medical reasoning over the
patient's clinical history. Do not search the internet for benchmark
answers.
