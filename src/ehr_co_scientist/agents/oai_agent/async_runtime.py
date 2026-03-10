"""Internal async task-state helpers used by the agent batch orchestrator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import aiolimiter

from ehr_co_scientist.backends.adapter import BackendConfig, run_chat_completion_async
from ehr_co_scientist.tools.tooling.runtime import ToolRuntime

from .parsing import extract_native_tool_calls, parse_tool_call
from .policy import check_tool_policy, should_simulate_tool_call_in_evaluation
from .tool_exec import execute_tool_call, simulate_tool_call_in_evaluation


@dataclass
class AsyncTaskState:
    task: dict[str, Any]
    messages: list[dict[str, Any]]
    tool_trace: list[dict[str, Any]]
    rounds_used: int = 0
    final_answer: str = ""
    backend_result: dict[str, Any] | None = None
    error: str | None = None
    terminated_early: bool = False
    termination_reason: str | None = None
    done: bool = False
    completion_recorded: bool = False


def new_task_state(task: dict[str, Any], system_prompt: str) -> AsyncTaskState:
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": task.get("instruction", "")})
    return AsyncTaskState(task=task, messages=messages, tool_trace=[])


def to_result_payload(state: AsyncTaskState, max_rounds: int) -> dict[str, Any]:
    if not state.done and state.rounds_used >= max_rounds:
        state.error = state.error or "max_rounds_exceeded"
    return {
        "final_answer": state.final_answer,
        "tool_trace": state.tool_trace,
        "rounds_used": state.rounds_used,
        "backend_result": state.backend_result,
        "error": state.error or ("max_rounds_exceeded" if not state.done else None),
        "terminated_early": state.terminated_early,
        "termination_reason": state.termination_reason,
    }


def apply_policy_result(state: AsyncTaskState, policy_result: dict[str, Any]) -> None:
    state.final_answer = str(policy_result.get("final_answer", ""))
    state.tool_trace = list(policy_result.get("tool_trace", state.tool_trace))
    state.rounds_used = int(policy_result.get("rounds_used", state.rounds_used))
    state.backend_result = policy_result.get("backend_result")
    state.error = policy_result.get("error")
    state.terminated_early = bool(policy_result.get("terminated_early", False))
    state.termination_reason = policy_result.get("termination_reason")
    state.done = True


async def advance_task_state(
    *,
    state: AsyncTaskState,
    backend_config: BackendConfig,
    max_rounds: int,
    evaluation_mode: bool,
    chat_kwargs: dict[str, Any] | None,
    allowed_tools: set[str] | None,
    tool_runtime_obj: ToolRuntime,
    limiter: aiolimiter.AsyncLimiter | None,
    retry_attempts: int,
) -> None:
    """Advance one task by a single backend turn, appending tool outputs when needed."""
    if state.done:
        return
    if state.rounds_used >= max_rounds:
        state.error = state.error or "max_rounds_exceeded"
        state.done = True
        return

    try:
        backend_result = await run_chat_completion_async(
            config=backend_config,
            messages=state.messages,
            limiter=limiter,
            retry_attempts=retry_attempts,
            **(chat_kwargs or {}),
        )
    except Exception as exc:  # noqa: BLE001
        state.error = str(exc)
        state.done = True
        return

    state.rounds_used += 1
    state.backend_result = backend_result
    raw_message, native_tool_calls = extract_native_tool_calls(backend_result)

    if raw_message is not None and native_tool_calls:
        state.messages.append(
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
                state.error = f"Invalid tool arguments for {function_name}: {exc}"

            policy_result = check_tool_policy(
                tool_trace=state.tool_trace,
                round_index=max(0, state.rounds_used - 1),
                tool_name=function_name,
                args=parsed_args,
                backend_result=backend_result,
                allowed_tools=allowed_tools,
            )
            if policy_result is not None:
                apply_policy_result(state, policy_result)
                return

            if should_simulate_tool_call_in_evaluation(
                evaluation_mode=evaluation_mode,
                tool_name=function_name,
            ):
                simulate_tool_call_in_evaluation(
                    tool_name=function_name,
                    args=parsed_args,
                    tool_trace=state.tool_trace,
                    messages=state.messages,
                    tool_call_id=tool_call.get("id"),
                )
                continue

            execution_error = execute_tool_call(
                tool_name=function_name,
                args=parsed_args,
                tool_runtime=tool_runtime_obj,
                tool_trace=state.tool_trace,
                messages=state.messages,
                tool_call_id=tool_call.get("id"),
            )
            if execution_error is not None:
                state.error = execution_error
        return

    assistant_text = backend_result["assistant_text"]
    state.messages.append({"role": "assistant", "content": assistant_text})

    parsed = parse_tool_call(assistant_text)
    if parsed is None:
        state.final_answer = assistant_text
        state.done = True
        return

    tool_name, args = parsed
    policy_result = check_tool_policy(
        tool_trace=state.tool_trace,
        round_index=max(0, state.rounds_used - 1),
        tool_name=tool_name,
        args=args,
        backend_result=backend_result,
        allowed_tools=allowed_tools,
    )
    if policy_result is not None:
        apply_policy_result(state, policy_result)
        return
    if should_simulate_tool_call_in_evaluation(
        evaluation_mode=evaluation_mode,
        tool_name=tool_name,
    ):
        simulate_tool_call_in_evaluation(
            tool_name=tool_name,
            args=args,
            tool_trace=state.tool_trace,
            messages=state.messages,
            tool_call_id=None,
        )
        return
    execution_error = execute_tool_call(
        tool_name=tool_name,
        args=args,
        tool_runtime=tool_runtime_obj,
        tool_trace=state.tool_trace,
        messages=state.messages,
        tool_call_id=None,
    )
    if execution_error is not None:
        state.error = execution_error
