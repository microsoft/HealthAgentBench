"""Tool execution helpers for agent tool-calling flows."""

from __future__ import annotations

import json
from typing import Any

from ehr_co_scientist.tools.catalog import TOOL_REGISTRY
from ehr_co_scientist.tools.tooling.function_tools import call_registered_tool
from ehr_co_scientist.tools.tooling.runtime import ToolRuntime

from .parsing import tool_feedback_message


def execute_tool_call(
    *,
    tool_name: str,
    args: dict[str, Any],
    tool_runtime: ToolRuntime,
    tool_trace: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    tool_call_id: str | None,
) -> str | None:
    """Dispatch a tool call, append trace/messages, and return error text if any."""
    try:
        tool_result = call_registered_tool(
            tool_name,
            tool_runtime,
            registry=TOOL_REGISTRY,
            kwargs=args,
        )
        tool_trace.append(
            {
                "tool": tool_name,
                "args": args,
                "result": tool_result,
                "status": "ok",
            }
        )
        if tool_call_id is not None:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(tool_result, ensure_ascii=True),
                }
            )
        else:
            messages.append(tool_feedback_message(tool_name, {"result": tool_result}))
        return None
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
        if tool_call_id is not None:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"error": last_error}, ensure_ascii=True),
                }
            )
        else:
            messages.append(tool_feedback_message(tool_name, {"error": last_error}))
        return last_error


def simulate_tool_call_in_evaluation(
    *,
    tool_name: str,
    args: dict[str, Any],
    tool_trace: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    tool_call_id: str | None,
) -> None:
    """Append simulated tool output for evaluation-mode write tools."""
    simulated_output = "The action has been taken. Please return the final answer."
    tool_trace.append(
        {
            "tool": tool_name,
            "args": args,
            "result": {"simulated": True, "message": simulated_output},
            "status": "simulated_evaluation_mode",
        }
    )
    if tool_call_id is not None:
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps({"message": simulated_output}, ensure_ascii=True),
            }
        )
    else:
        messages.append(tool_feedback_message(tool_name, {"message": simulated_output}))
