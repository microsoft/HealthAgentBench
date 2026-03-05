"""Parsing and message helpers for agent tool-calling flows."""

from __future__ import annotations

import json
from typing import Any


def parse_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    """Parse fallback assistant text as `{\"tool\": ..., \"args\": ...}` payload."""
    text = text.strip()
    if not text:
        return None

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


def tool_feedback_message(tool_name: str, payload: dict[str, Any]) -> dict[str, str]:
    """Build fallback tool feedback message for non-native tool-call loops."""
    return {
        "role": "user",
        "content": json.dumps(
            {"tool_name": tool_name, "tool_output": payload},
            ensure_ascii=True,
        ),
    }


def extract_native_tool_calls(
    backend_result: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Extract assistant message and tool calls from OpenAI-style raw payload."""
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
