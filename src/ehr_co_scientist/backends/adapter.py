"""Provider-neutral backend adapter used by experiment runners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ehr_co_scientist.backends import azure_openai


@dataclass(frozen=True)
class BackendConfig:
    backend: str
    model: str
    endpoint_name: str | None = None
    api_version: str | None = None
    api_key: str | None = None


def _extract_assistant_text(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message", {})
    if isinstance(message, dict):
        content = message.get("content", "")
        if isinstance(content, str):
            return content
    return ""


def run_chat_completion(
    *,
    config: BackendConfig,
    messages: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    """Run a chat completion and normalize the response envelope."""
    backend = config.backend.lower()

    if backend == "mock":
        text = kwargs.pop("mock_response", "mock_response")
        payload: dict[str, Any] = {
            "choices": [{"message": {"role": "assistant", "content": text}}],
            "model": config.model,
            "id": "mock-0",
        }
    elif backend == "azure_openai":
        response = azure_openai.run_direct_chat_completion(
            model=config.model,
            messages=messages,
            endpoint_name=config.endpoint_name,
            api_version=config.api_version or azure_openai.API_VERSION,
            api_key=config.api_key,
            **kwargs,
        )
        if hasattr(response, "model_dump"):
            payload = response.model_dump()
        elif hasattr(response, "to_dict"):
            payload = response.to_dict()
        else:
            raise TypeError(
                "Unsupported chat completion response type from azure backend."
            )
    else:
        raise ValueError(f"Unsupported backend: {config.backend}")

    return {
        "backend": config.backend,
        "model": config.model,
        "endpoint_name": config.endpoint_name,
        "api_version": config.api_version,
        "assistant_text": _extract_assistant_text(payload),
        "raw": payload,
    }
