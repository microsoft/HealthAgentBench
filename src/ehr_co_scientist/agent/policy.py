"""Policy and termination helpers for agent tool calls."""

from __future__ import annotations

from typing import Any

from ehr_co_scientist.tools.catalog import should_stop_on_call_in_evaluation


def build_early_termination(
    *,
    tool_trace: list[dict[str, Any]],
    round_index: int,
    tool_name: str,
    args: dict[str, Any],
    backend_result: dict[str, Any] | None,
    last_error: str | None,
) -> dict[str, Any]:
    """Build result payload for evaluation-mode write-tool short-circuit."""
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


def build_blocked_not_allowed(
    *,
    tool_trace: list[dict[str, Any]],
    round_index: int,
    tool_name: str,
    args: dict[str, Any],
    backend_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build result payload when a tool violates per-task allowlist policy."""
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


def check_tool_policy(
    *,
    tool_trace: list[dict[str, Any]],
    round_index: int,
    tool_name: str,
    args: dict[str, Any],
    backend_result: dict[str, Any] | None,
    allowed_tools: set[str] | None,
    evaluation_mode: bool,
    last_error: str | None,
) -> dict[str, Any] | None:
    """Evaluate runtime policy gates and return termination payload if blocked."""
    if allowed_tools is not None and tool_name not in allowed_tools:
        return build_blocked_not_allowed(
            tool_trace=tool_trace,
            round_index=round_index,
            tool_name=tool_name,
            args=args,
            backend_result=backend_result,
        )
    if evaluation_mode and should_stop_on_call_in_evaluation(tool_name):
        return build_early_termination(
            tool_trace=tool_trace,
            round_index=round_index,
            tool_name=tool_name,
            args=args,
            backend_result=backend_result,
            last_error=last_error,
        )
    return None
