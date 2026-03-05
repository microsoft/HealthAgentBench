from __future__ import annotations

from typing import Any

from ehr_co_scientist.agent import AgentConfig, run_task
from ehr_co_scientist.backends.adapter import BackendConfig


def test_run_task_uses_backend_safe_tool_feedback(monkeypatch):
    calls: list[list[dict[str, Any]]] = []

    def fake_chat_completion(*, config, messages):  # noqa: ANN001
        calls.append(messages)
        if len(calls) == 1:
            return {"assistant_text": '{"tool":"patient.search","args":{"name":"Alice"}}'}
        return {"assistant_text": "done"}

    def fake_call_tool(tool_name, client, **kwargs):  # noqa: ANN001
        assert tool_name == "patient.search"
        assert "registry" in kwargs
        assert "function_name_to_tool_name" in kwargs
        assert kwargs["kwargs"] == {"name": "Alice"}
        return {"resourceType": "Bundle", "total": 1}

    monkeypatch.setattr(
        "ehr_co_scientist.agent.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr("ehr_co_scientist.agent.call_registered_tool", fake_call_tool)

    result = run_task(
        task={"instruction": "find patient"},
        backend_config=BackendConfig(backend="mock", model="m"),
        fhir_base_url="http://localhost:8080/fhir",
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

    def fake_call_tool(tool_name, client, **kwargs):  # noqa: ANN001
        assert tool_name == "patient_search"
        assert kwargs["kwargs"] == {"name": "Alice"}
        return {"resourceType": "Bundle", "total": 1}

    monkeypatch.setattr(
        "ehr_co_scientist.agent.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr("ehr_co_scientist.agent.call_registered_tool", fake_call_tool)

    result = run_task(
        task={"instruction": "find patient"},
        backend_config=BackendConfig(backend="mock", model="m"),
        fhir_base_url="http://localhost:8080/fhir",
        config=AgentConfig(max_rounds=3),
        chat_kwargs={"tools": [{"type": "function", "function": {"name": "patient_search"}}]},
    )

    assert result["final_answer"] == "done"
    second_round_messages = calls[1]
    assert any(m.get("role") == "tool" for m in second_round_messages)


def test_run_task_evaluation_mode_ends_on_write_tool_fallback(monkeypatch):
    calls: list[list[dict[str, Any]]] = []

    def fake_chat_completion(*, config, messages):  # noqa: ANN001
        calls.append(messages)
        return {"assistant_text": '{"tool":"vital.create","args":{"resource":{"resourceType":"Observation"}}}'}

    def fail_call_tool(tool_name, client, **kwargs):  # noqa: ANN001
        raise AssertionError(f"call_tool should not run in evaluation mode: {tool_name}")

    monkeypatch.setattr(
        "ehr_co_scientist.agent.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr("ehr_co_scientist.agent.call_registered_tool", fail_call_tool)

    result = run_task(
        task={"instruction": "record BP"},
        backend_config=BackendConfig(backend="mock", model="m"),
        fhir_base_url="http://localhost:8080/fhir",
        config=AgentConfig(max_rounds=3, evaluation_mode=True),
    )

    assert result["terminated_early"] is True
    assert result["termination_reason"] == "evaluation_mode_write_tool_called"
    assert result["final_answer"] == ""
    assert result["tool_trace"][0]["tool"] == "vital.create"
    assert result["tool_trace"][0]["status"] == "skipped_evaluation_mode"


def test_run_task_evaluation_mode_ends_on_write_tool_native(monkeypatch):
    calls: list[list[dict[str, Any]]] = []

    def fake_chat_completion(*, config, messages, **kwargs):  # noqa: ANN001
        calls.append(messages)
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

    def fail_call_tool(tool_name, client, **kwargs):  # noqa: ANN001
        raise AssertionError(f"call_tool should not run in evaluation mode: {tool_name}")

    monkeypatch.setattr(
        "ehr_co_scientist.agent.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr("ehr_co_scientist.agent.call_registered_tool", fail_call_tool)

    result = run_task(
        task={"instruction": "record BP"},
        backend_config=BackendConfig(backend="mock", model="m"),
        fhir_base_url="http://localhost:8080/fhir",
        config=AgentConfig(max_rounds=3, evaluation_mode=True),
        chat_kwargs={"tools": [{"type": "function", "function": {"name": "vital_create"}}]},
    )

    assert result["terminated_early"] is True
    assert result["termination_reason"] == "evaluation_mode_write_tool_called"
    assert result["final_answer"] == ""
    assert result["tool_trace"][0]["tool"] == "vital_create"
    assert result["tool_trace"][0]["status"] == "skipped_evaluation_mode"


def test_run_task_blocks_disallowed_tool_fallback(monkeypatch):
    def fake_chat_completion(*, config, messages):  # noqa: ANN001
        return {"assistant_text": '{"tool":"vital.create","args":{"resource":{"resourceType":"Observation"}}}'}

    def fail_call_tool(tool_name, client, **kwargs):  # noqa: ANN001
        raise AssertionError(f"call_tool should not run for disallowed tool: {tool_name}")

    monkeypatch.setattr(
        "ehr_co_scientist.agent.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr("ehr_co_scientist.agent.call_registered_tool", fail_call_tool)

    result = run_task(
        task={"instruction": "record BP"},
        backend_config=BackendConfig(backend="mock", model="m"),
        fhir_base_url="http://localhost:8080/fhir",
        config=AgentConfig(max_rounds=3),
        allowed_tools={"patient.search"},
    )

    assert result["terminated_early"] is True
    assert result["termination_reason"] == "tool_not_allowed"
    assert result["tool_trace"][0]["status"] == "blocked_not_allowed"


def test_run_task_blocks_disallowed_tool_native(monkeypatch):
    def fake_chat_completion(*, config, messages, **kwargs):  # noqa: ANN001
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

    def fail_call_tool(tool_name, client, **kwargs):  # noqa: ANN001
        raise AssertionError(f"call_tool should not run for disallowed tool: {tool_name}")

    monkeypatch.setattr(
        "ehr_co_scientist.agent.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr("ehr_co_scientist.agent.call_registered_tool", fail_call_tool)

    result = run_task(
        task={"instruction": "record BP"},
        backend_config=BackendConfig(backend="mock", model="m"),
        fhir_base_url="http://localhost:8080/fhir",
        config=AgentConfig(max_rounds=3),
        chat_kwargs={"tools": [{"type": "function", "function": {"name": "vital_create"}}]},
        allowed_tools={"patient.search"},
    )

    assert result["terminated_early"] is True
    assert result["termination_reason"] == "tool_not_allowed"
    assert result["tool_trace"][0]["status"] == "blocked_not_allowed"
