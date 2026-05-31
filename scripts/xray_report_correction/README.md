# MIMIC-CXR Report Correction

This directory contains the Harbor-first integration for the MIMIC-CXR
radiology report **correction** benchmark task. Each task is one patient:
the agent sees the patient's prior chest-X-ray studies (JPGs + reports)
plus a **draft FINDINGS section pre-populated with deliberate clinical
errors** for the target study; the agent must **review and correct the
draft** by editing or deleting sentences (no new statements may be
added). The corrected FINDINGS is scored by the same CheXprompt judge
used by the generation task.

Correction tests radiology *editing* / *peer review* — recognizing and
fixing wrong assertions in a draft — rather than radiology *generation*
from scratch.

## Canonical Source and Canonical Runner

- Canonical upstream source: PhysioNet `mimic-cxr` v2.1.0 (reports) +
  `mimic-cxr-jpg` v2.1.0 (images + split CSV) — credentialed access
- Canonical Harbor task generator: `scripts/xray_report_correction/generate_harbor_tasks.py`
- Canonical runnable task artifact: `tasks/xray_report_correction/`
- Per-benchmark asset cache: `scripts/xray_report_correction/assets/` (gitignored)
- Verifier-side metric aggregator: `scripts/xray_report_correction/aggregate_metric.py`

## Benchmark Shape

This benchmark evaluates whether an agent can:

1. inspect a longitudinal patient directory at `/data/patient/` containing
   timestamped folders of prior studies (JPG images + `report.txt`) plus
   one target-study folder whose `report.txt` already includes a
   **draft FINDINGS section to correct**
2. view images via repeated tool calls and integrate visual observation
   with the textual history from prior reports
3. **edit or delete** statements in the draft FINDINGS to match the
   ground-truth findings; **adding new statements is not permitted**
   (the corrected report should stay close in scope and length to the
   draft)
4. emit a valid `/workspace/submission.json` with the corrected FINDINGS

The benchmark ships **10 curated cases** (`case_01..case_10`); the
ground-truth reports were manually reviewed for clinical accuracy. Each
case's draft is synthesized at bootstrap time by applying one or more
of seven documented swap principles to the gold FINDINGS (see
`generate_harbor_tasks.py` — `SWAP_RULES` dict and the comment block
that introduces it):

- **P1** Lateralization (left↔right)
- **P2** Severity modifier (mild↔severe, normal↔enlarged, etc.)
- **P3** Comparison-word flip (worsened↔improved, persistent↔resolved)
- **P4** No-prior / no-change → introduce change
- **P5** Count change (`three chest tubes` ↔ `two`)
- **P6** Location change (upper↔lower lobe, mid SVC↔proximal SVC, etc.)
- **P7** Explicit negation flip (gold's `no consolidation` → `focal
  consolidation`)

Measurements, acuity (acute↔chronic), diagnostic-category swaps
(atelectasis↔consolidation), additive findings, and removal of
findings affirmed in the gold are deliberately **out of scope** for
the counterfactual injection — they introduce ambiguity that the
agent can't resolve from the image alone.

Per-trial reward is binary: **1 iff a majority (≥3 of 5) CheXprompt
votes** (Microsoft's GPT-class judge) **report zero
clinically-significant errors** in the agent's corrected FINDINGS vs.
the gold, else 0. The aggregator emits mean reward (= pass rate),
integer pass count, and `mean_sig_errors` (diagnostic; lower is
better) via a `uv-script` metric hook.

## Canonical Workflow

> **Credentials required.** Two sets, both loaded from the repo-root
> `.env` automatically (the per-task `docker-compose.yaml` declares
> `env_file: ../../../../.env`, so no manual `export` is needed):
>
> * **PhysioNet** (`PN_USER` / `PN_PASS`) — credentialed access to
>   the two upstream MIMIC-CXR projects (same credential pair gates
>   both):
>
>     1. **MIMIC-CXR v2.1.0** — radiology reports
>        (https://physionet.org/content/mimic-cxr/2.1.0/). The
>        bootstrap service pulls per-patient prior-study `.txt`
>        files and the target study's `.txt` from
>        `files/p<group>/p<subject>/s<study>.txt` here.
>     2. **MIMIC-CXR-JPG v2.1.0** — chest-X-ray JPG frames + the
>        three small CSVs the generator needs to enumerate priors
>        (https://physionet.org/content/mimic-cxr-jpg/2.1.0/).
>        `setup.sh` downloads `mimic-cxr-2.0.0-metadata.csv.gz`,
>        `mimic-cxr-2.0.0-split.csv.gz`, and
>        `mimic-cxr-2.0.0-chexpert.csv.gz`; the bootstrap service
>        pulls per-patient JPG views from `files/p<group>/p<subject>/s<study>/<dicom>.jpg`.
>
>     To obtain `PN_USER` / `PN_PASS`: register a free PhysioNet
>     account, complete CITI "Data or Specimens Only Research"
>     training and upload the certificate to your profile, then
>     sign the Data Use Agreement on each of the two project pages
>     above. The same account credentials authenticate against both
>     projects.
> * **CheXprompt verifier model** — drives the verifier inside the trial
>   container. Supports both Azure OpenAI and vanilla OpenAI; whichever
>   set of vars is present in `.env` wins. The agent process never sees
>   these — they're forwarded to the verifier step only.
>
> **Default model: `gpt-5.4`.** If `CHEXPROMPT_DEPLOYMENT` (or its alias
> `AZURE_OPENAI_DEPLOYMENT`) is not set, the verifier hardcodes
> `gpt-5.4` as the deployment / model name. For Azure, your deployment
> alias must point at a gpt-5.4-capable resource.
>
> ### Azure OpenAI (recommended)
>
> Set in `.env`:
>
> ```
> AZURE_OPENAI_API_KEY=<your-azure-key>
> AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
> AZURE_OPENAI_API_VERSION=2024-02-15-preview
> AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>    # optional, defaults to "gpt-5.4"
> ```
>
> The verifier also accepts the legacy openai-SDK aliases
> (`OPENAI_API_BASE` for endpoint, `OPENAI_API_VERSION` for version,
> `OPENAI_API_KEY` for key, `CHEXPROMPT_DEPLOYMENT` for deployment) —
> Azure-canonical names take priority when both are set. Azure mode
> activates whenever endpoint + version + key are all present.
>
> ### Vanilla OpenAI (fallback)
>
> Set in `.env`:
>
> ```
> OPENAI_API_KEY=<your-key>
> OPENAI_BASE_URL=https://api.openai.com/v1   # optional; default if unset
> CHEXPROMPT_DEPLOYMENT=gpt-4o                # optional; default is gpt-5.4
> ```
>
> ### Model parameter handling
>
> `gpt-5.x` deployments (the default `gpt-5.4`) require
> `max_completion_tokens` instead of `max_tokens` and don't accept
> `temperature` / `top_p` / `frequency_penalty` / `presence_penalty`.
> The verifier auto-adapts when the deployment name starts with
> `gpt-5`. If your Azure deployment alias doesn't start with `gpt-5`
> but the underlying model is gpt-5.x, name the deployment with a
> `gpt-5*` prefix so the adaptation triggers.

```bash
# 0) Optional — Codex login (if running the agent under Harbor's Codex
#    adapter). Everything else is read from .env at run time.
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"

# 1) Download dataset-wide PhysioNet assets (metadata CSV, split CSV,
#    and CheXpert label CSV). NOTE: this directory's setup.sh skips
#    the multi-gigabyte mimic-cxr-reports.zip by default since the
#    per-trial bootstrap container fetches per-patient prior reports
#    on demand.
bash scripts/xray_report_correction/setup.sh

# 2) Generate the canonical Harbor task tree. ``--curated`` builds the
#    hardcoded 10-case set (``CURATED_CASES`` in
#    ``generate_harbor_tasks.py``) — patients whose target FINDINGS
#    were manually reviewed for clinical accuracy. Add ``--purge`` to
#    wipe any stale ``case_NN`` dirs at --output-root first.
uv run python scripts/xray_report_correction/generate_harbor_tasks.py \
  --output-root tasks/xray_report_correction --curated --purge

# 3) Run the Harbor task. The two-service docker-compose pattern's
#    `bootstrap` container downloads missing assets (per-patient JPGs
#    and the target report used by the verifier) from PhysioNet on
#    first use, AND appends the case's counterfactual draft FINDINGS
#    to the target study's report.txt so the agent sees a populated
#    `FINDINGS:` section to review.
#
#    IMPORTANT: ``jobs/xray_report_correction.yaml`` sets
#    ``disable_web_search: true`` (codex) and
#    ``disallowed_tools: "WebSearch WebFetch"`` (claude-code) on the
#    agent kwargs. These MUST stay on — without them the agent can
#    look up the gold report on public MIMIC-CXR mirrors by searching
#    distinctive phrases from the draft (we observed gpt-5.3-codex
#    doing exactly this, inflating its pass rate). When invoking the
#    multitask baseline launcher, also pass ``--disable-web-browser``
#    explicitly — that flag defaults to OFF on the launcher so it
#    does NOT silently apply to other tasks.
uv run harbor run -c jobs/xray_report_correction.yaml

# 4) (Optional) Multi-model baseline sweep. Same web-disable rule
#    applies: pass ``--disable-web-browser`` explicitly — the
#    multitask launcher defaults to internet ON.
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name xray_report_correction --task-path tasks \
  --harness codex \
  --model gpt-5.3-codex --model gpt-5.4 --model gpt-5.4-mini --model gpt-5.5 \
  --attempts 3 --concurrency 2 --reasoning-effort xhigh \
  --disable-web-browser \
  --metric-to-report success \
  --metric-to-report mean_pass_rate \
  --metric-to-report mean_sig_errors \
  --baselines-md paper/baselines.md

# Repeat for the claude-code harness (same flags, swap --harness +
# --model values to the claude family).
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name xray_report_correction --task-path tasks \
  --harness claude-code \
  --model claude-opus-4-6 --model claude-opus-4-7 \
  --model claude-opus-4-8 --model claude-sonnet-4-6 \
  --attempts 3 --concurrency 2 --reasoning-effort xhigh \
  --disable-web-browser \
  --metric-to-report success \
  --metric-to-report mean_pass_rate \
  --metric-to-report mean_sig_errors \
  --baselines-md paper/baselines.md
```

## Evaluation

Reward signal: **CheXprompt** (https://github.com/microsoft/chexprompt)
prompts a GPT-class deployment (Azure OpenAI or vanilla OpenAI;
default `gpt-5.4`) to count clinical errors in 6 categories × 2
severity tiers for the agent's corrected FINDINGS vs. the gold
FINDINGS. A trial **passes** (reward 1.0) iff a majority (≥3 of 5)
CheXprompt votes report zero *clinically-significant* errors;
otherwise the trial fails (reward 0.0). The gold FINDINGS is parsed
at verifier time from the target study's full report (staged at
`/tests/target_report.txt` by the `bootstrap` compose service via
the credentialed PhysioNet download).

The curated 10 cases have been manually reviewed for clinical
accuracy of the gold. The gold text is never checked into this repo
and is never exposed to the agent at runtime. The
counterfactual draft FINDINGS the agent sees IS checked in (as a
Python string constant in the generator), so each `--curated` build
is fully reproducible.

## Counterfactual Design

The corrupted draft FINDINGS is synthesized **at bootstrap time** by
applying a per-case list of `(gold_phrase, cf_phrase)` substitutions to
the real gold FINDINGS pulled from PhysioNet. See
`generate_harbor_tasks.py::SWAP_RULES` for the full rule list (10
cases × 3–8 swaps each, 52 swaps total) and the seven principle
categories the swaps draw from (listed in **Benchmark Shape** above).

Why per-rule rather than per-case hardcoded strings:

- **No gold leakage at rest.** The committed task tree carries swap
  rules, not the corrupted draft text. A reader of the repo (or a
  scraper indexing it) cannot reconstruct the gold by inverting the
  swap unless they also have PhysioNet credentials.
- **Loud failure on rule rot.** If MIMIC-CXR ever re-words a gold
  report, `apply_swap_rules` raises at bootstrap time
  (`swap source phrase missing from FINDINGS: ...`) instead of
  silently writing the unmodified gold.
- **Single source of truth.** Both the host-side smoke test
  (`tests/test_xray_report_correction_swap_rules.py`) and the
  in-container bootstrap apply the same rules; drift between them is
  impossible by construction.

## Harbor Artifacts

The Harbor job at `jobs/xray_report_correction.yaml` retains this
artifact after each run for error analysis:

- `/workspace/submission.json` — the agent's corrected FINDINGS

## Manual Replay

See [`debug/xray_report_correction/README.md`](../../debug/xray_report_correction/README.md)
for the in-container manual replay path used to distinguish agent
failures from task / environment / verifier failures.

## References

- **MIMIC-CXR paper**: https://doi.org/10.1038/s41597-019-0322-0
- **MIMIC-CXR v2.1.0**: https://physionet.org/content/mimic-cxr/2.1.0/
- **MIMIC-CXR-JPG v2.1.0**: https://physionet.org/content/mimic-cxr-jpg/2.1.0/
- **CheXprompt** (verifier model): https://github.com/microsoft/chexprompt
- **ExecPlan**: `.agent/plans/xray_report_correction.md`
