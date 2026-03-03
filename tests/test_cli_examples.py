import json

from ehr_co_scientist.backends import azure_openai


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    def to_dict(self) -> dict[str, str]:
        return {"content": self._content}


def test_batch_cli_example_command(monkeypatch, capsys):
    captured: dict[str, object] = {}

    def _fake_run_batch_chat_completion(**kwargs):
        captured.update(kwargs)
        return [_FakeResponse("model_is_deployment_batch_ok")]

    monkeypatch.setattr(
        azure_openai,
        "run_batch_chat_completion",
        _fake_run_batch_chat_completion,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "ehr-azure-openai",
            "--example",
            "batch",
            "--endpoint-name",
            "trapi-msrhf-shared",
            "--model",
            "o3_2025-04-16",
            "--prompt",
            "Reply with exactly: model_is_deployment_batch_ok",
            "--reasoning-effort",
            "low",
        ],
    )

    azure_openai.main()

    output = json.loads(capsys.readouterr().out)
    assert output[0]["content"] == "model_is_deployment_batch_ok"
    assert captured["endpoint_name"] == "trapi-msrhf-shared"
    assert captured["model"] == "o3_2025-04-16"
    assert captured["reasoning_effort"] == "low"


def test_batch_cli_function_calling_flags(monkeypatch, capsys):
    captured: dict[str, object] = {}

    def _fake_run_batch_chat_completion(**kwargs):
        captured.update(kwargs)
        return [_FakeResponse("tool_calling_ok")]

    monkeypatch.setattr(
        azure_openai,
        "run_batch_chat_completion",
        _fake_run_batch_chat_completion,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "ehr-azure-openai",
            "--example",
            "batch",
            "--endpoint-name",
            "trapi-msrhf-shared",
            "--model",
            "o3_2025-04-16",
            "--prompt",
            "Use tools.",
            "--function-name",
            "get_weather",
            "--function-description",
            "Get weather by city.",
            "--function-parameters-json",
            '{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}',
            "--tool-choice",
            "function:get_weather",
            "--parallel-tool-calls",
            "false",
        ],
    )

    azure_openai.main()

    output = json.loads(capsys.readouterr().out)
    assert output[0]["content"] == "tool_calling_ok"

    assert captured["parallel_tool_calls"] is False
    assert captured["tool_choice"] == {"type": "function", "function": {"name": "get_weather"}}
    assert captured["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather by city.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]
