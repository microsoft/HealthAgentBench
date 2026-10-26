# `xray_report_correction_case_01`

This is one of 10 `xray_report_correction_*` tasks in the **X-ray Report Correction** category of [HealthAgentBench](../../README.md).

Given a MIMIC-CXR study, correct the radiology report FINDINGS. The submission is scored by the CheXprompt LLM-judge verifier, which counts clinically-significant errors against the reference report.

**Success criteria:** reward 1.0 iff the report has **zero** clinically-significant errors judged by LLM-judge CheXprompt verifier's majority vote.

> **Credentials required.** MIMIC-CXR is PhysioNet-gated — set `PN_USER` / `PN_PASS` in `.env`. Scoring also needs an OpenAI-compatible judge (`CHEXPROMPT_OPENAI_API_KEY` / `CHEXPROMPT_OPENAI_BASE_URL`, or the Azure `CHEXPROMPT_AZURE_OPENAI_*` variables). See [Setting up task access](../../README.md#setting-up-task-access) and [Setting up other secrets](../../README.md#setting-up-other-secrets).

## Run this task

```bash
uv run harbor run \
  --env-file .env \
  --path tasks/xray_report_correction_case_01 \
  --agent claude-code \
  --model claude-opus-4-8 \
  --agent-kwarg reasoning_effort=xhigh \
  --agent-kwarg disallowed_tools="WebSearch WebFetch" \
  --n-attempts 3 --n-concurrent 5
```

## Run the whole X-ray Report Correction category

Point `--path` at `tasks/` and glob the category name with `--include-task-name` (quote it so the shell doesn't expand the `*`):

```bash
uv run harbor run \
  --env-file .env \
  --path tasks \
  --include-task-name "xray_report_correction_*" \
  --agent claude-code \
  --model claude-opus-4-8 \
  --agent-kwarg reasoning_effort=xhigh \
  --agent-kwarg disallowed_tools="WebSearch WebFetch" \
  --n-attempts 3 --n-concurrent 5
```

## Data & references

Each case's gold report is downloaded from PhysioNet by the task's bootstrap step at runtime (not stored in the repo).

- MIMIC-CXR v2.1.0: <https://physionet.org/content/mimic-cxr/2.1.0/>
- CheXprompt (Chaves et al.): <https://github.com/microsoft/chexprompt>
