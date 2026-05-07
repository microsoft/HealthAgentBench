# Clinical Trial Matching (TREC Clinical Trials 2021)

Patient-to-clinical-trial retrieval benchmark. Each task hands the agent
one synthetic patient admission note plus a per-topic corpus of clinical
trial documents, and asks the agent to rank the trials by how well the
patient matches them. The verifier scores the ranking with NDCG@10
against the upstream physician-judged qrels.

## Canonical sources and runners

- Upstream task spec: <https://www.trec-cds.org/2021.html>
- Upstream topics + qrels: <https://trec.nist.gov/data/trials2021.html>
- Upstream corpus snapshot (April 27, 2021): five zip parts at
  `https://www.trec-cds.org/2021_data/ClinicalTrials.2021-04-27.partN.zip`
  (~1.7 GB total, ~400 K trials).
- Canonical Harbor task generator:
  `scripts/clinical_trial_matching/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/clinical_trial_matching/`
- Per-benchmark asset cache: `scripts/clinical_trial_matching/assets/`
  (the `raw_cache/` subdirectory is gitignored — `task_configs.yaml`
  is the only committed asset)
- Verifier-side metric aggregator:
  `scripts/clinical_trial_matching/aggregate_metric.py`

## Benchmark shape

10 tasks, one per topic. Each task evaluates whether an agent can:

1. Read one synthetic patient case at `/workspace/data/topic.txt` (a
   typical admission note, 5–10 sentences with diagnoses, comorbidities,
   medications, and procedures).
2. Inspect the per-topic candidate trials at
   `/workspace/data/trials/<NCT_ID>.xml` (typically 300–620 files), each
   conforming to the ClinicalTrials.gov v1 XML schema.
3. Emit a TREC-format ranked run file at `/workspace/submission/run.txt`
   with up to 1000 rows of `TOPIC_NO Q0 NCT_ID RANK SCORE RUN_NAME`.

The verifier computes `NDCG@10`, `NDCG@1000`, and `recall@1000` with
`pytrec_eval` against the per-topic qrels slice. NDCG@10 is the reward.

## Selected topics

Stratified by clinical specialty and patient demographics, with NDCG
stability filters (≥ 50 eligible trials, ≥ 400 total judged):

- Topic 8 — 57M, CLL → Richter's transformation (oncology)
- Topic 75 — 55M, Parkinson's disease (neurology)
- Topic 19 — 65M, CAD/MI/VT (cardiovascular)
- Topic 6 — 55F, ESRD on HD + recurrent C. diff (renal + infectious)
- Topic 14 — 70 y/o, COPD + OSA + obesity hypoventilation (pulmonary)
- Topic 29 — 24M, T1DM ×11 yr (endocrine)
- Topic 26 — 45F, autoimmune w/ abdominal pain (rheumatology)
- Topic 35 — 15F, recurrent bilateral migraines (paediatric neurology)
- Topic 27 — 53M, chronic HCV ×2 yr (GI/hepatology)
- Topic 45 — 34M, sickle cell disease (haematology)

## Canonical workflow

```bash
# 1. Codex login (the agent runtime needs ~/.codex/auth.json on the host).
codex login status

# 2. Generate the task tree. First run pre-fetches the per-topic NCT
#    corpus into scripts/clinical_trial_matching/assets/raw_cache/
#    via HTTP range requests on the upstream zip parts. ~1-2 min the
#    first time, instant on subsequent runs.
uv run python scripts/clinical_trial_matching/generate_harbor_tasks.py \
    --output-root tasks/clinical_trial_matching

# 3. Run the Harbor job.
uv run harbor run -c jobs/clinical_trial_matching.yaml
```

## Data flow

The host directory `scripts/clinical_trial_matching/assets/raw_cache/`
is gitignored. It holds two kinds of files:

- `topics2021.xml`, `qrels2021.txt` — small (combined ~1 MB), fetched
  by the generator on first run.
- `<NCT_ID>.xml` — clinical-trial documents (avg ~20 KB each, ~85 MB
  total across the 4,570 unique NCTs needed by the 10 selected topics).
  Pre-fetched by `generate_harbor_tasks.py`; also fetched lazily by
  the per-task `entrypoint.sh` if any are missing on first
  `harbor run`.

The host cache is bind-mounted into each task container at
`/data/_cache` (read-write) via the per-task `docker-compose.yaml`
override. The task `entrypoint.sh`:

1. Re-grants write permissions (a previous run may have chmod'd ro).
2. Acquires `flock 9` on `/data/_cache/.locks/topic_<id>.lock` so two
   concurrent containers for the same topic do not race the same
   files.
3. Calls `fetch_trials.py --cache-dir /data/_cache --out
   /workspace/data/trials`. Cache hits are copied locally; missing
   NCTs are downloaded from the upstream zip parts via HTTP range
   requests, written into both the cache (chmod 0444) and the
   workspace.
4. After the fetch, `chmod -R a-w /data/_cache` so the agent (or
   any later step) cannot mutate cached files.
5. Releases the lock and `exec`s the rest of the original CMD chain
   (Harbor exec's the agent into the running container).

This makes the very first `harbor run` self-sufficient — even without
the host pre-fetch — and makes every subsequent run nearly instantaneous.

## Anti-cheat

The benchmark is publicly judged, so a sufficiently motivated agent
could in principle look up the qrels file. Mitigations:

- Source-name obfuscation: `instruction.md` does not mention TREC,
  ClinicalTrials.gov, or qrels.
- Container internet access is enabled (the entrypoint needs it for
  the bootstrap fetch). The agent runtime has internet too; the
  `instruction.md` explicitly forbids the agent from using the
  internet to look up answers. This is best-effort.

## Manual replay

Inside a generated task container (after `harbor run` builds the image):

```bash
# Stage data (already done by the entrypoint, but you can re-run).
python /workspace/fetch_trials.py \
    --ids /workspace/trial_ncts.txt \
    --out /workspace/data/trials \
    --cache-dir /data/_cache

# Hand-craft a near-perfect submission against the qrels for sanity-check
# (only available on the host side, not inside the container — you'd
# need to mount the qrels in or copy them).
```

Run the verifier separately:

```bash
docker compose run --rm main python /tests/verify.py
cat /logs/verifier/reward.json
```

## References

- TREC Clinical Trials 2021 track home:
  <https://www.trec-cds.org/2021.html>
- Related-work note: `design/related_work/clinical_trial_matching.md`
- ExecPlan: `.agent/plans/clinical_trial_matching_execplan.md`
