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
        assert kwargs == {"name": "Alice"}
        return {"resourceType": "Bundle", "total": 1}

    monkeypatch.setattr(
        "ehr_co_scientist.agent.run_chat_completion", fake_chat_completion
    )
    monkeypatch.setattr("ehr_co_scientist.agent.call_tool", fake_call_tool)

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
