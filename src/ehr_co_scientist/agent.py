"""Core agent loop for tool-augmented MedAgentBench-style tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ehr_co_scientist.backends.adapter import BackendConfig, run_chat_completion
from ehr_co_scientist.tools.catalog import (
    TOOL_REGISTRY,
    should_stop_on_call_in_evaluation,
)
from ehr_co_scientist.tools.tooling.function_tools import (
    call_registered_tool,
)
from ehr_co_scientist.tools.tooling.runtime import ToolRuntime


@dataclass(frozen=True)
class AgentConfig:
    max_rounds: int = 8
    evaluation_mode: bool = False


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


def _extract_native_tool_calls(
    backend_result: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    raw = backend_result.get("raw")
    if not isinstance(raw, dict):
        return None, []
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        return None, []
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return None, []
    tool_calls = message.get("tool_calls")
    if not isinstance(tool_calls, list) or not tool_calls:
        return message, []
    valid_calls = [call for call in tool_calls if isinstance(call, dict)]
    return message, valid_calls


def _build_early_termination(
    *,
    tool_trace: list[dict[str, Any]],
    round_index: int,
    tool_name: str,
    args: dict[str, Any],
    backend_result: dict[str, Any] | None,
    last_error: str | None,
) -> dict[str, Any]:
    return {
        "final_answer": "",
        "tool_trace": tool_trace
        + [
            {
                "tool": tool_name,
                "args": args,
                "status": "skipped_evaluation_mode",
                "stop_reason": "evaluation_mode_write_tool_called",
            }
        ],
        "rounds_used": round_index + 1,
        "backend_result": backend_result,
        "error": last_error,
        "terminated_early": True,
        "termination_reason": "evaluation_mode_write_tool_called",
    }


def _build_blocked_not_allowed(
    *,
    tool_trace: list[dict[str, Any]],
    round_index: int,
    tool_name: str,
    args: dict[str, Any],
    backend_result: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "final_answer": "",
        "tool_trace": tool_trace
        + [
            {
                "tool": tool_name,
                "args": args,
                "status": "blocked_not_allowed",
                "stop_reason": "tool_not_allowed",
            }
        ],
        "rounds_used": round_index + 1,
        "backend_result": backend_result,
        "error": f"Tool not allowed by task policy: {tool_name}",
        "terminated_early": True,
        "termination_reason": "tool_not_allowed",
    }


def _check_tool_policy(
    *,
    tool_trace: list[dict[str, Any]],
    round_index: int,
    tool_name: str,
    args: dict[str, Any],
    backend_result: dict[str, Any] | None,
    allowed_tools: set[str] | None,
    cfg: AgentConfig,
    last_error: str | None,
) -> dict[str, Any] | None:
    if allowed_tools is not None and tool_name not in allowed_tools:
        return _build_blocked_not_allowed(
            tool_trace=tool_trace,
            round_index=round_index,
            tool_name=tool_name,
            args=args,
            backend_result=backend_result,
        )
    if cfg.evaluation_mode and should_stop_on_call_in_evaluation(tool_name):
        return _build_early_termination(
            tool_trace=tool_trace,
            round_index=round_index,
            tool_name=tool_name,
            args=args,
            backend_result=backend_result,
            last_error=last_error,
        )
    return None


def _execute_tool_call(
    *,
    tool_name: str,
    args: dict[str, Any],
    tool_runtime: ToolRuntime,
    tool_trace: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    tool_call_id: str | None,
) -> str | None:
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
            messages.append(_tool_feedback_message(tool_name, {"result": tool_result}))
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
            messages.append(_tool_feedback_message(tool_name, {"error": last_error}))
        return last_error


def run_task(
    *,
    task: dict[str, Any],
    backend_config: BackendConfig,
    tool_runtime: ToolRuntime | None = None,
    config: AgentConfig | None = None,
    chat_kwargs: dict[str, Any] | None = None,
    allowed_tools: set[str] | None = None,
) -> dict[str, Any]:
    cfg = config or AgentConfig()
    tool_runtime_obj = tool_runtime or ToolRuntime()

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
        backend_result = run_chat_completion(
            config=backend_config,
            messages=messages,
            **(chat_kwargs or {}),
        )
        raw_message, native_tool_calls = _extract_native_tool_calls(backend_result)

        if raw_message is not None and native_tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": raw_message.get("content") or "",
                    "tool_calls": native_tool_calls,
                }
            )
            for tool_call in native_tool_calls:
                function_payload = tool_call.get("function", {})
                function_name = function_payload.get("name")
                raw_args = function_payload.get("arguments", "{}")
                if not isinstance(function_name, str):
                    continue
                try:
                    parsed_args = json.loads(raw_args)
                    if not isinstance(parsed_args, dict):
                        raise ValueError("tool arguments must decode to an object")
                except Exception as exc:  # noqa: BLE001
                    parsed_args = {}
                    last_error = f"Invalid tool arguments for {function_name}: {exc}"
                policy_result = _check_tool_policy(
                    tool_trace=tool_trace,
                    round_index=round_index,
                    tool_name=function_name,
                    args=parsed_args,
                    backend_result=backend_result,
                    allowed_tools=allowed_tools,
                    cfg=cfg,
                    last_error=last_error,
                )
                if policy_result is not None:
                    return policy_result
                execution_error = _execute_tool_call(
                    tool_name=function_name,
                    args=parsed_args,
                    tool_runtime=tool_runtime_obj,
                    tool_trace=tool_trace,
                    messages=messages,
                    tool_call_id=tool_call.get("id"),
                )
                if execution_error is not None:
                    last_error = execution_error
            continue

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
                "terminated_early": False,
                "termination_reason": None,
            }

        tool_name, args = parsed
        policy_result = _check_tool_policy(
            tool_trace=tool_trace,
            round_index=round_index,
            tool_name=tool_name,
            args=args,
            backend_result=backend_result,
            allowed_tools=allowed_tools,
            cfg=cfg,
            last_error=last_error,
        )
        if policy_result is not None:
            return policy_result
        execution_error = _execute_tool_call(
            tool_name=tool_name,
            args=args,
            tool_runtime=tool_runtime_obj,
            tool_trace=tool_trace,
            messages=messages,
            tool_call_id=None,
        )
        if execution_error is not None:
            last_error = execution_error

    return {
        "final_answer": "",
        "tool_trace": tool_trace,
        "rounds_used": cfg.max_rounds,
        "backend_result": None,
        "error": last_error or "max_rounds_exceeded",
        "terminated_early": False,
        "termination_reason": None,
    }
