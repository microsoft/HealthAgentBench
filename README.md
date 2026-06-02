<img src="logo.png" alt="MedCLI" width="120" />

## Overview

MedCLI is a [Harbor](https://harborframework.com/)-first research project exploring how LLM agents can act as autonomous research assistants for healthcare.

The system centers on a **terminal-based** environment where agents can inspect clinical data, use tools, access medical resources, and iteratively reason through complex tasks. Through this interface, agents interact with EHR systems and common data models to explore data, answer questions, perform analyses, and take structured actions.

MedCLI is designed to study how agents can **understand and operate on real-world medical data systems** across tasks such as:

| Task | Description |
|------|-------------|
| **Schema understanding** | Explore and document EHR database structure (tables, schemas, relationships) |
| **Factual QA** | Answer data-grounded clinical questions with SQL + reasoning |
| **Cross-schema ETL** | Map source EHR to target CDM (OMOP, FHIR, MEDS) with validation |
| **Cohort construction** | Assemble patient cohorts from natural-language inclusion/exclusion criteria |
| **Outcome prediction** | Retrieve features, find similar patients, produce risk estimates with evidence |
| **Trajectory summarization** | Generate longitudinal clinical summaries for a given patient |
| **Temporal reasoning** | Answer multi-hop temporal queries with time-window logic |
| **Treatment pathway analysis** | Extract and visualize common treatment sequences for a condition |
| **Trial eligibility** | Assess clinical trial eligibility for a patient with structured evidence |
| **Medication reconciliation** | Compile active medications and flag drug interactions |
| **Data quality auditing** | Detect inconsistencies, missing values, and implausible entries |
| **Report generation** | Draft clinical documents (referral letters, discharge summaries) from data |
| **Data aggregation** | Aggregate multiple EHR measurements into computed summaries or trends |
| **Clinical data recording** | Record new observations or updates into the clinical chart via structured APIs |
| **Care ordering** | Place orders/referrals/tests with appropriate coded payloads and rationale |

## Harbor Background

This project uses Harbor as the terminal-task execution and evaluation substrate. Harbor provides a consistent trial lifecycle (agent run, verifier run, and artifacts), while MedCLI adds domain-specific health tasks, Harbor task environments, and benchmark integrations.

Important pointers:

1. Harbor repo: https://github.com/harbor-framework/harbor
2. Harbor docs/wiki: https://deepwiki.com/harbor-framework/harbor
3. Stable Harbor version used here: `0.3.0`
   - Upgrade caution: Harbor upgrades can break custom installed-agent integration interfaces such as `src/medcli/agents/harbor/installed/codex.py` and `src/medcli/agents/harbor/installed/copilot_cli.py`.
4. Local Harbor job configs in this repo include `jobs/example.yaml` and benchmark-specific job configs under `jobs/`.

## Project Structure

```text
MedCLI/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── PLANS.md
├── .agent/plans/               # ExecPlans, including Harbor migration and cleanup plans
├── design/                     # Design docs, brainstorm notes, and planning materials not yet executed in the project
├── paper/                      # Manuscript draft, paper framing, and later paper-writing materials such as LaTeX sources
├── tasks/<benchmark>/          # Generated Harbor task for a benchmark
├── jobs/                       # Harbor job configs
├── debug/                      # Generic Harbor-oriented debug helpers and docs
├── src/medcli/
│   └── agents/harbor/installed/ # Harbor installed-agent wrappers
├── scripts/<benchmark>/        # Benchmark-specific setup, generation, and evaluation helpers
├── results/                    # Run and evaluation artifacts (gitignored)
└── tests/
```

## Setup

```bash
# Clone the repo
git clone git@github.com:sheng-z/MedCLI.git
cd MedCLI

# Install dependencies
uv sync --all-extras
```

Python version requirement: `>=3.12`.

### Benchmark-specific data access

Some benchmarks require gated datasets and per-user credentials before the
container can run. Each is documented in its own `scripts/<benchmark>/README.md`:

- **EHRSHOT** — Redivis dataset (Stanford SHAH lab). Needs an accepted DUA + an
  API token at `~/.redivis/api_token`. See [`scripts/ehrshot/README.md`](scripts/ehrshot/README.md).
- **ct_abnormality** — CT-RATE (Hugging Face, OpenRAIL gated). Accept the
  dataset agreement, then set `HF_TOKEN` in `.env`; the per-task bootstrap
  service reads it via `env_file`. See
  [`scripts/ct_abnormality/README.md`](scripts/ct_abnormality/README.md).
- **xray_report_correction** — Two PhysioNet credentialed-access projects,
  both gated by a single `PN_USER` / `PN_PASS` pair in `.env`:
  [MIMIC-CXR v2.1.0](https://physionet.org/content/mimic-cxr/2.1.0/) for the
  radiology reports and [MIMIC-CXR-JPG v2.1.0](https://physionet.org/content/mimic-cxr-jpg/2.1.0/)
  for the JPG frames + the metadata / split / chexpert CSVs. Register a
  PhysioNet account, complete CITI "Data or Specimens Only Research"
  training, then sign the DUA on each project page. See
  [`scripts/xray_report_correction/README.md`](scripts/xray_report_correction/README.md).

Set these up once per host before invoking the corresponding Harbor task.

### Other project-level secrets file (`.env`)

`.env` is gitignored (see `.gitignore`). Create one at the repo root for any
credentials the launchers / docker-compose need to read from the host
environment. The schema (no real secrets) is:

```bash
# ----- Verifier model credentials (xray_report_correction / CheXprompt) -----
# Pick ONE of the two paths below. The verifier's _configure_openai_for_chexprompt
# detects which is present and routes accordingly.
#
# (a) Azure OpenAI — preferred. Activates when endpoint + version + key are all set.
# The verifier accepts both AZURE_OPENAI_* (canonical) and OPENAI_API_* (legacy)
# names — set whichever your environment provides. Endpoint also accepts
# AZURE_OPENAI_BASE_URL.
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_VERSION=2024-02-15-preview
# AZURE_OPENAI_DEPLOYMENT (alias: CHEXPROMPT_DEPLOYMENT) — optional; defaults to gpt-5.4
# Your Azure deployment alias should serve gpt-5.4 (or another gpt-5.x model) so
# the verifier's reasoning-model param adaptation triggers.
AZURE_OPENAI_DEPLOYMENT=
#
# (b) Vanilla OpenAI — fallback. Activates when (a) is not fully present.
# OPENAI_API_KEY=
# OPENAI_BASE_URL=https://api.openai.com/v1
# CHEXPROMPT_DEPLOYMENT=gpt-4o   # optional; if omitted, defaults to gpt-5.4

# ----- Dataset access (gated downloads at task bootstrap) -----
# PhysioNet credentials (xray_report_correction).
PN_USER=
PN_PASS=
# Hugging Face token (ct_abnormality / CT-RATE, OpenRAIL gated). The per-task
# bootstrap service reads this via env_file; main/the agent never sees it.
HF_TOKEN=
```

**CheXprompt verifier default model.** If neither `CHEXPROMPT_DEPLOYMENT` nor
`AZURE_OPENAI_DEPLOYMENT` is set, the verifier in
`scripts/xray_report_correction/harbor_evaluator.py` hardcodes `gpt-5.4` as the
deployment / model name. For Azure, ensure your deployment alias resolves
to a gpt-5.4-capable resource (or override with one of those env vars).

Populate it with your real values and load before any Harbor run:

```bash
chmod 600 .env
set -a && . ./.env && set +a    # exports every variable in .env into the shell
```

For variables a task bootstrap needs (e.g. `PN_USER` / `PN_PASS` to download a
gated PhysioNet snapshot), reference them via `${PN_USER}` in the task's
`docker-compose.yaml` `environment:` section so docker substitutes them at
compose-up time. For variables the agent harness itself reads
(`OPENAI_API_KEY`, `OPENAI_BASE_URL`), pass through with
`harbor run --ae OPENAI_API_KEY="$OPENAI_API_KEY"` or have them already in the
launcher process's environment (`set -a && . ./.env && set +a` above is enough).


## Harness Authentication

The Harbor multitask launcher and `harbor run` need credentials forwarded to the
agent container for each harness. The `require_<harness>_auth()` checks in
`scripts/run_harbor_baselines_multitask.py` enforce these contracts.

### codex (`--harness codex`)

Two routes supported by `medcli.agents.harbor.installed.codex.Codex`:

**(a) ChatGPT login** — keep the local Codex CLI logged in so
`~/.codex/auth.json` exists, then export its contents:

```bash
codex login status                                   # verify local login
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"   # forwarded into container
# Override the default path with CODEX_AUTH_FILE if your auth.json lives elsewhere.
```

**(b) Azure OpenAI** — bypasses ChatGPT login. The wrapper reads your local
`~/.codex/config.toml` and forwards every host env var referenced by an
`env_key` field on a `[model_providers.*]` table. Configure providers there
once, export the keys, and any job YAML that uses this wrapper picks them up
without further wiring.

Example `~/.codex/config.toml` with two endpoints:

```toml
model = "gpt-5.4"
model_provider = "azure_eus"

[model_providers.azure_wus3]
name = "Azure OpenAI (West US 3)"
base_url = "https://hanoveroai.openai.azure.com/openai/v1"
env_key = "AZURE_OPENAI_WUS3_API_KEY"
wire_api = "responses"

[model_providers.azure_eus]
name = "Azure OpenAI (East US)"
base_url = "https://hanoveroaieus.openai.azure.com/openai/v1"
env_key = "AZURE_OPENAI_EUS_API_KEY"
wire_api = "responses"
```

Then on the host:

```bash
export AZURE_OPENAI_WUS3_API_KEY=<your-key>
export AZURE_OPENAI_EUS_API_KEY=<your-key>
```

The wrapper uploads the config file into the container at
`$CODEX_HOME/config.toml`. Providers whose `env_key` is unset on the host are
skipped silently — at least one must resolve, or the wrapper aborts with a
clear error. Override the config path with `CODEX_CONFIG_FILE` (useful in CI).

### copilot-cli (`--harness copilot-cli`)

Set a GitHub token (any of these is accepted, in priority order):

```bash
export GH_TOKEN=$(cat ~/.github_credentials/github_pat)
# or: gh auth login   (and let the harness pick up `gh auth token`)
# or: export COPILOT_GITHUB_TOKEN=...
# or: export GITHUB_TOKEN=...
```

### claude-code (`--harness claude-code`)

Either rely on an existing Claude Code session — the launcher auto-loads
`~/.claude/.credentials.json` (`claudeAiOauth.accessToken`) — or export
explicitly:

```bash
export CLAUDE_CODE_OAUTH_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.claude/.credentials.json'))['claudeAiOauth']['accessToken'])")
# or: export ANTHROPIC_API_KEY=<your-key>     # standard Anthropic API
# or: export CLAUDE_CODE_USE_BEDROCK=1        # plus AWS creds
# Override the credentials file path with CLAUDE_CODE_AUTH_FILE.
```

## Usage

See `tasks/README.md` for the full list of currently supported tasks and benchmarks.

```bash
# Ensure your harness's auth is set (see "Harness Authentication" below)
uv run harbor run -c jobs/<benchmark>.yaml
```

For multi-model baseline sweeps:

```bash
uv run python scripts/run_harbor_baselines_multitask.py \
    --task-name <benchmark> --task-path tasks \
    --harness <codex|copilot-cli|claude-code> \
    --model <model-1> --model <model-2> \
    --attempts 3 --concurrency 2 \
    --metrics-script scripts/<benchmark>/aggregate_metric.py \
    --metric-to-report f1 --metric-to-report recall --metric-to-report precision \
    --baselines-md paper/baselines.md
```

**Web search / web fetch are allowed by default.** Both baseline launchers
accept `--disable-web-browser` (default `False`) and, when passed, translate it
per harness so the agent's built-in browsing tools can't be used to look up gold
answers:

- `codex` → appends `-c web_search="disabled"` to the `codex exec` command
- `claude-code` → appends `--disallowedTools "WebSearch WebFetch"` to the `claude`
  command
- `copilot-cli` → no upstream toggle; the flag is silently skipped

Pass `--disable-web-browser` explicitly for benchmarks where the gold answer
(or a recognisable phrase from it) is reachable via a public mirror or general
web search — for example `xray_report_correction` over MIMIC-CXR, where we
observed `gpt-5.3-codex` retrieving the gold report by searching distinctive
draft phrases. Leave the default in place for benchmarks like `ehr_to_meds_etl`
where the agent legitimately needs to fetch a public web page.

When invoking Harbor directly with `uv run harbor run -c jobs/<benchmark>.yaml`
(no launcher), set the same toggles on each agent's `kwargs` inside the job
YAML. Example:

```yaml
agents:
  - import_path: medcli.agents.harbor.installed.codex:Codex
    model_name: gpt-5.5
    kwargs:
      reasoning_effort: xhigh
      # Forwards to ``-c web_search="disabled"`` on the codex CLI.
      disable_web_search: true

  - import_path: medcli.agents.harbor.installed.claude_code:ClaudeCode
    model_name: claude-opus-4-7
    kwargs:
      reasoning_effort: xhigh
      # Forwards to ``--disallowedTools "WebSearch WebFetch"`` on the
      # claude CLI; the bare tool names remove WebSearch/WebFetch from
      # the model's context entirely (deny rules take precedence over
      # ``bypassPermissions`` mode).
      disallowed_tools: "WebSearch WebFetch"
```

These are the same kwargs the launchers inject when
`--disable-web-browser` is on; setting them in the YAML keeps the
guarantee when calling Harbor directly.

## Task Creation

For the canonical repo-level workflow for adding a new benchmark, see [`design/benchmark_addition_workflow.md`](design/benchmark_addition_workflow.md). Once the task is built, run through [`design/human_review.md`](design/human_review.md) before merging — it's the canonical pre-merge checklist humans should review. 

For benchmark-specific task creation details, see `scripts/<benchmark>/README.md`.

## Debug

For generic Harbor debug workflow details, see `debug/README.md`.

For benchmark-specific debug workflow details, see `debug/<benchmark>/README.md`.

## License

TBD
