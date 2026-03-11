from __future__ import annotations

import asyncio
from typing import Any

import pytest

from medcli.agents.oai_agent import AgentConfig, run_async_tasks, run_task
from medcli.backends.adapter import BackendConfig


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
        "medcli.agents.oai_agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "medcli.agents.oai_agent.tool_exec.call_registered_tool", fake_call_tool
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
        "medcli.agents.oai_agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "medcli.agents.oai_agent.tool_exec.call_registered_tool", fake_call_tool
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
def test_run_task_evaluation_mode_simulates_write_tool(monkeypatch, native_tool_call):
    calls: list[list[dict[str, Any]]] = []

    def fake_chat_completion(*, config, messages, **kwargs):  # noqa: ANN001
        calls.append(messages)
        if len(calls) == 1 and native_tool_call:
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
        if len(calls) == 1:
            return {"assistant_text": '{"tool":"vital_create","args":{"resource":{"resourceType":"Observation"}}}'}
        return {"assistant_text": "final response"}

    def fail_call_tool(tool_name, tool_runtime, **kwargs):  # noqa: ANN001
        raise AssertionError(f"call_tool should not run in evaluation mode: {tool_name}")

    monkeypatch.setattr(
        "medcli.agents.oai_agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "medcli.agents.oai_agent.tool_exec.call_registered_tool", fail_call_tool
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

    assert result["terminated_early"] is False
    assert result["termination_reason"] is None
    assert result["final_answer"] == "final response"
    assert result["tool_trace"][0]["tool"] == "vital_create"
    assert result["tool_trace"][0]["status"] == "simulated_evaluation_mode"

    second_round_messages = calls[1]
    if native_tool_call:
        assert any(
            m.get("role") == "tool"
            and m.get("content")
            == '{"message": "The action has been taken. Please return the final answer."}'
            for m in second_round_messages
        )
    else:
        assert any(
            m.get("role") == "user"
            and "The action has been taken. Please return the final answer."
            in str(m.get("content", ""))
            for m in second_round_messages
        )


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
        "medcli.agents.oai_agent.core.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "medcli.agents.oai_agent.tool_exec.call_registered_tool", fail_call_tool
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


def test_run_async_tasks_requeues_after_tool_output(monkeypatch):
    async def fake_chat_completion_async(*, config, messages, **kwargs):  # noqa: ANN001
        instruction = str(messages[1].get("content", ""))
        if instruction == "task-a":
            has_tool_feedback = any(
                m.get("role") == "user" and "tool_output" in str(m.get("content", ""))
                for m in messages
            )
            if not has_tool_feedback:
                return {
                    "assistant_text": '{"tool":"patient_search","args":{"name":"Alice"}}'
                }
            return {"assistant_text": "done-a"}
        return {"assistant_text": "done-b"}

    def fake_call_tool(tool_name, tool_runtime, **kwargs):  # noqa: ANN001
        assert tool_name == "patient_search"
        return {"resourceType": "Bundle", "total": 1}

    monkeypatch.setattr(
        "medcli.agents.oai_agent.async_runtime.run_chat_completion_async",
        fake_chat_completion_async,
    )
    monkeypatch.setattr(
        "medcli.agents.oai_agent.tool_exec.call_registered_tool",
        fake_call_tool,
    )

    results = asyncio.run(
        run_async_tasks(
            tasks=[
                {"task_id": "a", "instruction": "task-a"},
                {"task_id": "b", "instruction": "task-b"},
            ],
            backend_config=BackendConfig(backend="mock", model="m"),
            config=AgentConfig(max_rounds=4),
            max_concurrency=2,
        )
    )

    assert len(results) == 2
    assert results[0]["final_answer"] == "done-a"
    assert results[0]["rounds_used"] == 2
    assert results[0]["tool_trace"][0]["tool"] == "patient_search"
    assert results[1]["final_answer"] == "done-b"
    assert results[1]["rounds_used"] == 1
