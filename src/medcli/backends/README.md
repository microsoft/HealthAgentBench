# Backends

This directory contains backend integrations used by the MedCLI project.

## Purpose

Backends provide model/service-specific client logic while keeping the rest of the
system decoupled from provider details (auth, endpoint routing, request options).

## Current Backends

- `azure_openai.py`
  - Azure OpenAI backend with:
    - named endpoint selection (`--endpoint-name`)
    - Entra ID or API key auth
    - direct and batch chat completion modes
    - retry/backoff for transient failures
    - optional function-calling flags (`tools`, `tool_choice`, `parallel_tool_calls`)

## Quick Usage

From repository root:

```bash
uv run medcli-azure-openai --help
```

Direct mode example:

```bash
uv run medcli-azure-openai \
  --example direct \
  --endpoint-name hanover-openai-east \
  --model gpt-5.2 \
  --prompt "Reply with exactly: ok"
```

Batch mode example:

```bash
uv run medcli-azure-openai \
  --example batch \
  --endpoint-name trapi-msrhf-shared \
  --model o3_2025-04-16 \
  --prompt "Reply with exactly: ok"
```

Function-calling example:

```bash
# tools.json:
# [
#   {
#     "type": "function",
#     "function": {
#       "name": "get_weather",
#       "description": "Get current weather by city.",
#       "parameters": {
#         "type": "object",
#         "properties": {"city": {"type": "string"}},
#         "required": ["city"]
#       }
#     }
#   }
# ]
#
uv run medcli-azure-openai \
  --example direct \
  --endpoint-name hanover-openai-east \
  --model gpt-5.2 \
  --prompt "What is the weather in Seattle? Use the tool." \
  --tools tools.json \
  --tool-choice function:get_weather \
  --parallel-tool-calls false
```

## Adding New Backends

When introducing a new backend module in this folder:

1. Add the new file (for example, `my_backend.py`).
2. Document it in the **Current Backends** section.
3. Add at least one minimal usage example.
4. Note any required environment variables or auth assumptions.
5. Update `pyproject.toml` scripts if a new CLI entrypoint is exposed.

This README should remain the single index for backend modules.
