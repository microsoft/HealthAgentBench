"""Core agent loop for tool-augmented MedAgentBench-style tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ehr_co_scientist.backends.adapter import BackendConfig, run_chat_completion
from ehr_co_scientist.tools.tooling.runtime import ToolRuntime

from .parsing import extract_native_tool_calls, parse_tool_call
from .policy import check_tool_policy, should_simulate_tool_call_in_evaluation
from .tool_exec import execute_tool_call, simulate_tool_call_in_evaluation


@dataclass(frozen=True)
class AgentConfig:
    """Execution limits and policy toggles for one agent run."""

    max_rounds: int = 8
    evaluation_mode: bool = False


def _system_prompt() -> str:
    return (
        "You are a clinical EHR assistant. Use tools when needed. "
        "When finished, provide a concise final answer."
    )


def run_task(
    *,
    task: dict[str, Any],
    backend_config: BackendConfig,
    tool_runtime: ToolRuntime | None = None,
    config: AgentConfig | None = None,
    chat_kwargs: dict[str, Any] | None = None,
    allowed_tools: set[str] | None = None,
) -> dict[str, Any]:
    """Run one task through iterative model/tool interaction.

    The loop supports both native tool-calling responses and the legacy
    JSON-in-text fallback format.
    """
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
        raw_message, native_tool_calls = extract_native_tool_calls(backend_result)

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
                policy_result = check_tool_policy(
                    tool_trace=tool_trace,
                    round_index=round_index,
                    tool_name=function_name,
                    args=parsed_args,
                    backend_result=backend_result,
                    allowed_tools=allowed_tools,
                )
                if policy_result is not None:
                    return policy_result
                if should_simulate_tool_call_in_evaluation(
                    evaluation_mode=cfg.evaluation_mode,
                    tool_name=function_name,
                ):
                    simulate_tool_call_in_evaluation(
                        tool_name=function_name,
                        args=parsed_args,
                        tool_trace=tool_trace,
                        messages=messages,
                        tool_call_id=tool_call.get("id"),
                    )
                    continue
                execution_error = execute_tool_call(
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

        parsed = parse_tool_call(assistant_text)
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
        policy_result = check_tool_policy(
            tool_trace=tool_trace,
            round_index=round_index,
            tool_name=tool_name,
            args=args,
            backend_result=backend_result,
            allowed_tools=allowed_tools,
        )
        if policy_result is not None:
            return policy_result
        if should_simulate_tool_call_in_evaluation(
            evaluation_mode=cfg.evaluation_mode,
            tool_name=tool_name,
        ):
            simulate_tool_call_in_evaluation(
                tool_name=tool_name,
                args=args,
                tool_trace=tool_trace,
                messages=messages,
                tool_call_id=None,
            )
            continue
        execution_error = execute_tool_call(
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
