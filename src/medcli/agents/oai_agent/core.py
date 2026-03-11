"""Core agent loop for tool-augmented MedAgentBench-style tasks."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import aiolimiter
from tqdm import tqdm

from medcli.backends.adapter import BackendConfig, run_chat_completion
from medcli.tools.tooling.runtime import ToolRuntime

from .async_runtime import (
    advance_task_state,
    new_task_state,
    to_result_payload,
)
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


async def run_async_tasks(
    *,
    tasks: list[dict[str, Any]],
    backend_config: BackendConfig,
    tool_runtime: ToolRuntime | None = None,
    config: AgentConfig | None = None,
    chat_kwargs: dict[str, Any] | None = None,
    chat_kwargs_by_task_id: dict[str, dict[str, Any] | None] | None = None,
    allowed_tools_by_task_id: dict[str, set[str]] | None = None,
    max_concurrency: int = 16,
    requests_per_minute: int | None = None,
    retry_attempts: int = 3,
    show_progress: bool = True,
) -> list[dict[str, Any]]:
    """Run multiple tasks concurrently with step-wise requeue after tool calls.

    Each backend response advances one task step; when a tool call is returned,
    tool output is appended to that task's message history and the task is put
    back on the queue for another backend turn.
    """
    cfg = config or AgentConfig()
    tool_runtime_obj = tool_runtime or ToolRuntime()
    states = [new_task_state(task, _system_prompt()) for task in tasks]
    queue: asyncio.Queue[int | None] = asyncio.Queue()
    for idx in range(len(states)):
        queue.put_nowait(idx)

    limiter = (
        aiolimiter.AsyncLimiter(requests_per_minute)
        if requests_per_minute is not None and requests_per_minute > 0
        else None
    )
    progress_lock = asyncio.Lock()
    steps_bar = (
        tqdm(desc="requests", unit="req", leave=True, dynamic_ncols=True)
        if show_progress
        else None
    )
    tasks_bar = (
        tqdm(total=len(states), desc="tasks", unit="task", leave=True, dynamic_ncols=True)
        if show_progress
        else None
    )

    async def _worker() -> None:
        while True:
            idx = await queue.get()
            if idx is None:
                queue.task_done()
                break
            state = states[idx]
            task_id = str(state.task.get("task_id", ""))
            allowed_tools = (
                (allowed_tools_by_task_id or {}).get(task_id)
                if allowed_tools_by_task_id is not None
                else None
            )
            resolved_chat_kwargs = (
                (chat_kwargs_by_task_id or {}).get(task_id)
                if chat_kwargs_by_task_id is not None
                else chat_kwargs
            )
            await advance_task_state(
                state=state,
                backend_config=backend_config,
                max_rounds=cfg.max_rounds,
                evaluation_mode=cfg.evaluation_mode,
                chat_kwargs=resolved_chat_kwargs,
                allowed_tools=allowed_tools,
                tool_runtime_obj=tool_runtime_obj,
                limiter=limiter,
                retry_attempts=retry_attempts,
            )
            async with progress_lock:
                if steps_bar is not None:
                    steps_bar.update(1)
            if not state.done and state.rounds_used < cfg.max_rounds:
                await queue.put(idx)
            elif not state.done and state.rounds_used >= cfg.max_rounds:
                state.error = state.error or "max_rounds_exceeded"
                state.done = True
            if state.done and not state.completion_recorded:
                async with progress_lock:
                    if tasks_bar is not None:
                        tasks_bar.update(1)
                state.completion_recorded = True
            queue.task_done()

    worker_count = max(1, min(max_concurrency, len(states) or 1))
    workers = [asyncio.create_task(_worker()) for _ in range(worker_count)]
    await queue.join()
    for _ in workers:
        queue.put_nowait(None)
    await asyncio.gather(*workers)
    if steps_bar is not None:
        steps_bar.close()
    if tasks_bar is not None:
        tasks_bar.close()

    return [to_result_payload(state, cfg.max_rounds) for state in states]
