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
- **ct_abnormality** — CT-RATE (Hugging Face, OpenRAIL gated). Needs a HF token
  at `~/.cache/huggingface/token`.

Set these up once per host before invoking the corresponding Harbor task.

### Other project-level secrets file (`.env`)

`.env` is gitignored (see `.gitignore`). Create one at the repo root for any
credentials the launchers / docker-compose need to read from the host
environment. The schema (no real secrets) is:

```bash
# ----- Verifier model credentials (xray_report_gen / CheXprompt) -----
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
# PhysioNet credentials (xray_report_gen).
PN_USER=
PN_PASS=
```

**CheXprompt verifier default model.** If neither `CHEXPROMPT_DEPLOYMENT` nor
`AZURE_OPENAI_DEPLOYMENT` is set, the verifier in
`scripts/xray_report_gen/harbor_evaluator.py` hardcodes `gpt-5.4` as the
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

**(b) Azure OpenAI API token** — bypasses ChatGPT login. Both env vars are
required:

```bash
export AZURE_OPENAI_API_KEY=<your-key>
export CODEX_TASK_TOML='model = "gpt-5.4"
model_provider = "azure"

[model_providers.azure]
name = "Azure OpenAI"
base_url = ""
env_key = "AZURE_OPENAI_API_KEY"
wire_api = "responses"'
```

The wrapper writes `$CODEX_TASK_TOML` to `$CODEX_HOME/config.toml` inside the
container so the codex CLI picks up the Azure provider config.

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
# `--ak disallow_web_search=true` disables the agent's WebSearch / WebFetch tools
# (claude-code) or `tools.web_search=false` (codex) so the agent cannot look up
# benchmark answers online; remove the flag only if the task legitimately needs it.
uv run harbor run -c jobs/<benchmark>.yaml --ak disallow_web_search=true
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

### Benchmark integrity: web-search is OFF by default

`scripts/run_harbor_baselines_multitask.py` **always passes
`disallow_web_search=true` to every agent** so the model cannot use
claude-code's `WebFetch` / `WebSearch` tools or codex's `web_search` tool.
This prevents the agent from looking up gold answers, datasets, or
upstream benchmark mirrors online.

- **Do not remove this default.** Every baseline sweep used to populate
  `paper/baselines.md` must run with web-search disabled so the recorded
  AUROC / pass-rate numbers reflect the agent's own reasoning, not its
  ability to web-search the benchmark.
- The only legitimate opt-out is `--allow-web-search`, reserved for
  benchmarks whose task is *itself* a web-retrieval task (none today).
  Adding `--allow-web-search` to a sweep that populates `baselines.md`
  invalidates the result for paper-quality reporting.
- The same flag flows into raw `uv harbor run` invocations via the job
  YAML: each agent's `kwargs:` block should include
  `disallow_web_search: true`. The medcli adapters
  ([src/medcli/agents/harbor/installed/](src/medcli/agents/harbor/installed/))
  translate the boolean into harness-specific CLI flags
  (claude: `--disallowedTools WebFetch,WebSearch`;
  codex: `-c tools.web_search=false`).

## Task Creation

For the canonical repo-level workflow for adding a new benchmark, see `design/benchmark_addition_workflow.md`.

For benchmark-specific task creation details, see `scripts/<benchmark>/README.md`.

## Debug

For generic Harbor debug workflow details, see `debug/README.md`.

For benchmark-specific debug workflow details, see `debug/<benchmark>/README.md`.

## License

TBD
