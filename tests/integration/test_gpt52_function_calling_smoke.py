from __future__ import annotations

import json
import os
from typing import Any

import pytest

from medcli.backends.azure_openai import run_direct_chat_completion


def _extract_tool_call(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Missing choices in chat completion response.")

    message = choices[0].get("message", {})
    if not isinstance(message, dict):
        raise RuntimeError("Missing assistant message in chat completion response.")

    tool_calls = message.get("tool_calls")
    if not isinstance(tool_calls, list) or not tool_calls:
        raise RuntimeError("Expected at least one tool call in assistant message.")

    first_call = tool_calls[0]
    if not isinstance(first_call, dict):
        raise RuntimeError("Tool call is not an object.")

    function_obj = first_call.get("function")
    if not isinstance(function_obj, dict):
        raise RuntimeError("Tool call missing function payload.")

    name = function_obj.get("name")
    if not isinstance(name, str) or not name:
        raise RuntimeError("Tool call missing function name.")

    raw_args = function_obj.get("arguments", "{}")
    if not isinstance(raw_args, str):
        raise RuntimeError("Tool call arguments must be a JSON string.")

    parsed_args = json.loads(raw_args)
    if not isinstance(parsed_args, dict):
        raise RuntimeError("Tool call arguments must decode to an object.")

    return name, parsed_args


@pytest.mark.integration
def test_gpt52_function_calling_smoke():
    if os.environ.get("RUN_AZURE_FUNCTION_CALLING_SMOKE") != "1":
        pytest.skip(
            "Set RUN_AZURE_FUNCTION_CALLING_SMOKE=1 to run gpt-5.2 function-calling smoke test."
        )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "add_numbers",
                "description": "Adds two integers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer"},
                    },
                    "required": ["a", "b"],
                },
            },
        }
    ]
    response = run_direct_chat_completion(
        model="gpt-5.2",
        messages=[
            {
                "role": "user",
                "content": (
                    "Call add_numbers with a=2 and b=3. "
                    "Return the function call only."
                ),
            }
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "add_numbers"}},
        parallel_tool_calls=False,
        temperature=0,
    )
    payload = response.to_dict()
    function_name, arguments = _extract_tool_call(payload)

    assert function_name == "add_numbers"
    assert arguments == {"a": 2, "b": 3}
    assert int(arguments["a"]) + int(arguments["b"]) == 5
