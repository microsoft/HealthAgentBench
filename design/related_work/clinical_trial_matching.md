# Clinical Trial Matching (TREC Clinical Trials 2021)

The MedCLI integration is named `clinical_trial_matching`. Source benchmark
is TREC Clinical Trials 2021 (TREC-CT 2021).

## Source

- Track home: <https://www.trec-cds.org/2021.html>
- NIST data page (topics + qrels): <https://trec.nist.gov/data/trials2021.html>
- Corpus: April 27, 2021 snapshot of ClinicalTrials.gov (5 zip files, ~1.7 GB total, ~400 K trials)
- Topics file: `topics2021.xml` (75 synthetic patient cases, ~5–10 sentences each, admission-note style)
- Judgments file: `qrels2021.txt` (35,832 rows, format `topic_no 0 NCT_id judgment` with judgment ∈ {0, 1, 2})
- Evaluation tooling: NIST [`trec_eval`](https://trec.nist.gov/trec_eval/) (or its Python port `pytrec_eval`)

## Task

The TREC Clinical Trials track flips the typical "trial → patients" recruitment paradigm into a "patient → trials" retrieval task. Each topic is a free-text patient case description that simulates an EHR admission note. The benchmark asks systems to retrieve a ranked list of clinical trial NCT IDs from the snapshot corpus that the patient is *eligible* for (meets inclusion criteria, no exclusion hits).

### Judgment scheme

Three graded relevance levels, judged by physicians from the OHSU Department of Medical Informatics:

- `0` non-relevant — trial unrelated to patient (24,243 rows).
- `1` excluded — patient meets inclusion criteria but is *excluded* by an exclusion criterion (6,019 rows).
- `2` eligible — patient meets inclusion AND not excluded (5,570 rows).

Per-topic eligibility counts range 6–203, median ~70. Per-topic total judged trials range 301–616, mean ~478.

### Evaluation metric

Normalized Discounted Cumulative Gain (NDCG) using the graded labels. Standard cut-offs are NDCG@10 and NDCG@1000. The `trec_eval` linear-gain form is `DCG = Σ rel_i / log₂(i+1)` summed over the top-k ranks; `NDCG@k = DCG@k / IDCG@k` ∈ [0, 1].

### Submission format (TREC ad-hoc retrieval)

    TOPIC_NO Q0 NCT_ID RANK SCORE RUN_NAME

Sorted by topic ascending then score descending. Up to 1000 IDs per topic.

## Why it is medically meaningful

NIH estimates 80% of clinical trials fail their recruitment timeline; many fail to recruit the minimum patient count needed to power the study. Patient-to-trial matching from EHR data is one of the highest-leverage AI applications in clinical operations. The TREC-CT benchmark is the largest publicly judged collection for this task and the de-facto standard for evaluating retrieval-style trial matching.

## Why it fits MedCLI

- The patient topic is exactly the kind of free-text admission note an EHR-aware agent should reason over.
- The agent must combine clinical concept understanding (conditions, medications, procedures) with structured retrieval over a non-trivial document corpus.
- The judgment scheme rewards distinguishing inclusion-met-but-excluded from genuinely eligible — pushing systems beyond surface keyword match.
- NDCG via `trec_eval` is a well-understood, publicly trusted IR metric.

## Notes

- Topics and qrels are public; agents with internet access could in principle look up qrels. The MedCLI integration should obscure benchmark provenance in agent-visible artifacts and either disable container internet or warn against lookup in `instruction.md`.
- The ClinicalTrials.gov XML schema is reasonably stable, but the snapshot is what the qrels were built against. Use the April 27, 2021 snapshot (not live API) for benchmark fidelity.
