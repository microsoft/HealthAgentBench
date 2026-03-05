from __future__ import annotations

from typing import Any

import pytest

from ehr_co_scientist.agent import AgentConfig, run_task
from ehr_co_scientist.backends.adapter import BackendConfig


def test_run_task_uses_backend_safe_tool_feedback(monkeypatch):
    calls: list[list[dict[str, Any]]] = []

    def fake_chat_completion(*, config, messages):  # noqa: ANN001
        calls.append(messages)
        if len(calls) == 1:
            return {"assistant_text": '{"tool":"patient_search","args":{"name":"Alice"}}'}
        return {"assistant_text": "done"}

    def fake_call_tool(tool_name, tool_runtime, **kwargs):  # noqa: ANN001
        assert tool_name == "patient_search"
        assert "registry" in kwargs
        assert "runtime" not in kwargs
        assert kwargs["kwargs"] == {"name": "Alice"}
        return {"resourceType": "Bundle", "total": 1}

    monkeypatch.setattr(
        "ehr_co_scientist.agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "ehr_co_scientist.agent.tool_exec.call_registered_tool", fake_call_tool
    )

    result = run_task(
        task={"instruction": "find patient"},
        backend_config=BackendConfig(backend="mock", model="m"),
        config=AgentConfig(max_rounds=3),
    )

    assert result["final_answer"] == "done"
    second_round_messages = calls[1]
    assert not any(m.get("role") == "tool" for m in second_round_messages)
    assert any(
        m.get("role") == "user" and "tool_output" in str(m.get("content", ""))
        for m in second_round_messages
    )


def test_run_task_handles_native_tool_calls(monkeypatch):
    calls: list[list[dict[str, Any]]] = []

    def fake_chat_completion(*, config, messages, **kwargs):  # noqa: ANN001
        calls.append(messages)
        if len(calls) == 1:
            return {
                "assistant_text": "",
                "raw": {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "patient_search",
                                            "arguments": '{"name":"Alice"}',
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            }
        return {"assistant_text": "done", "raw": {"choices": [{"message": {"role": "assistant", "content": "done"}}]}}

    def fake_call_tool(tool_name, tool_runtime, **kwargs):  # noqa: ANN001
        assert tool_name == "patient_search"
        assert kwargs["kwargs"] == {"name": "Alice"}
        return {"resourceType": "Bundle", "total": 1}

    monkeypatch.setattr(
        "ehr_co_scientist.agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "ehr_co_scientist.agent.tool_exec.call_registered_tool", fake_call_tool
    )

    result = run_task(
        task={"instruction": "find patient"},
        backend_config=BackendConfig(backend="mock", model="m"),
        config=AgentConfig(max_rounds=3),
        chat_kwargs={"tools": [{"type": "function", "function": {"name": "patient_search"}}]},
    )

    assert result["final_answer"] == "done"
    second_round_messages = calls[1]
    assert any(m.get("role") == "tool" for m in second_round_messages)


@pytest.mark.parametrize("native_tool_call", [False, True])
def test_run_task_evaluation_mode_ends_on_write_tool(monkeypatch, native_tool_call):
    calls: list[list[dict[str, Any]]] = []

    def fake_chat_completion(*, config, messages, **kwargs):  # noqa: ANN001
        calls.append(messages)
        if native_tool_call:
            return {
                "assistant_text": "",
                "raw": {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "vital_create",
                                            "arguments": '{"resource":{"resourceType":"Observation"}}',
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            }
        return {"assistant_text": '{"tool":"vital_create","args":{"resource":{"resourceType":"Observation"}}}'}

    def fail_call_tool(tool_name, tool_runtime, **kwargs):  # noqa: ANN001
        raise AssertionError(f"call_tool should not run in evaluation mode: {tool_name}")

    monkeypatch.setattr(
        "ehr_co_scientist.agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "ehr_co_scientist.agent.tool_exec.call_registered_tool", fail_call_tool
    )

    result = run_task(
        task={"instruction": "record BP"},
        backend_config=BackendConfig(backend="mock", model="m"),
        config=AgentConfig(max_rounds=3, evaluation_mode=True),
        chat_kwargs=(
            {"tools": [{"type": "function", "function": {"name": "vital_create"}}]}
            if native_tool_call
            else None
        ),
    )

    assert result["terminated_early"] is True
    assert result["termination_reason"] == "evaluation_mode_write_tool_called"
    assert result["final_answer"] == ""
    assert result["tool_trace"][0]["tool"] == "vital_create"
    assert result["tool_trace"][0]["status"] == "skipped_evaluation_mode"


@pytest.mark.parametrize("native_tool_call", [False, True])
def test_run_task_blocks_disallowed_tool(monkeypatch, native_tool_call):
    def fake_chat_completion(*, config, messages, **kwargs):  # noqa: ANN001
        if native_tool_call:
            return {
                "assistant_text": "",
                "raw": {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "vital_create",
                                            "arguments": '{"resource":{"resourceType":"Observation"}}',
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            }
        return {"assistant_text": '{"tool":"vital_create","args":{"resource":{"resourceType":"Observation"}}}'}

    def fail_call_tool(tool_name, tool_runtime, **kwargs):  # noqa: ANN001
        raise AssertionError(f"call_tool should not run for disallowed tool: {tool_name}")

    monkeypatch.setattr(
        "ehr_co_scientist.agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "ehr_co_scientist.agent.tool_exec.call_registered_tool", fail_call_tool
    )

    result = run_task(
        task={"instruction": "record BP"},
        backend_config=BackendConfig(backend="mock", model="m"),
        config=AgentConfig(max_rounds=3),
        chat_kwargs=(
            {"tools": [{"type": "function", "function": {"name": "vital_create"}}]}
            if native_tool_call
            else None
        ),
        allowed_tools={"patient_search"},
    )

    assert result["terminated_early"] is True
    assert result["termination_reason"] == "tool_not_allowed"
    assert result["tool_trace"][0]["status"] == "blocked_not_allowed"
