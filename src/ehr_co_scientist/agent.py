"""Core agent loop for tool-augmented MedAgentBench-style tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ehr_co_scientist.backends.adapter import BackendConfig, run_chat_completion
from ehr_co_scientist.tools.fhir_client import FHIRClient
from ehr_co_scientist.tools.fhir_tools import call_tool


@dataclass(frozen=True)
class AgentConfig:
    max_rounds: int = 8


def _system_prompt() -> str:
    return (
        "You are a clinical EHR assistant. Use tools when needed. "
        "When finished, provide a concise final answer."
    )


def _parse_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    text = text.strip()
    if not text:
        return None

    # Primary format: JSON object with fields tool/tool_name and args.
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    tool_name = payload.get("tool") or payload.get("tool_name")
    args = payload.get("args", {})
    if isinstance(tool_name, str) and isinstance(args, dict):
        return tool_name, args
    return None


def _tool_feedback_message(tool_name: str, payload: dict[str, Any]) -> dict[str, str]:
    # Keep tool feedback in a user-role message to stay compatible across chat backends
    # when no native function-calling tool_call_id flow is active.
    return {
        "role": "user",
        "content": json.dumps(
            {"tool_name": tool_name, "tool_output": payload},
            ensure_ascii=True,
        ),
    }


def run_task(
    *,
    task: dict[str, Any],
    backend_config: BackendConfig,
    fhir_base_url: str,
    config: AgentConfig | None = None,
) -> dict[str, Any]:
    cfg = config or AgentConfig()
    client = FHIRClient(base_url=fhir_base_url)

    messages: list[dict[str, Any]] = [{"role": "system", "content": _system_prompt()}]
    messages.append(
        {
            "role": "user",
            "content": task.get("instruction", ""),
        }
    )

    tool_trace: list[dict[str, Any]] = []
    last_error: str | None = None

    for round_index in range(cfg.max_rounds):
        backend_result = run_chat_completion(config=backend_config, messages=messages)
        assistant_text = backend_result["assistant_text"]
        messages.append({"role": "assistant", "content": assistant_text})

        parsed = _parse_tool_call(assistant_text)
        if parsed is None:
            return {
                "final_answer": assistant_text,
                "tool_trace": tool_trace,
                "rounds_used": round_index + 1,
                "backend_result": backend_result,
                "error": last_error,
            }

        tool_name, args = parsed
        try:
            tool_result = call_tool(tool_name, client, **args)
            tool_trace.append(
                {
                    "tool": tool_name,
                    "args": args,
                    "result": tool_result,
                    "status": "ok",
                }
            )
            messages.append(
                _tool_feedback_message(tool_name, {"result": tool_result})
            )
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            tool_trace.append(
                {
                    "tool": tool_name,
                    "args": args,
                    "status": "error",
                    "error": last_error,
                }
            )
            messages.append(
                _tool_feedback_message(tool_name, {"error": last_error})
            )

    return {
        "final_answer": "",
        "tool_trace": tool_trace,
        "rounds_used": cfg.max_rounds,
        "backend_result": None,
        "error": last_error or "max_rounds_exceeded",
    }
