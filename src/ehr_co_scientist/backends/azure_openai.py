"""Azure OpenAI helper utilities for internal TRAPI-style endpoints.

This module wraps model endpoint selection, AAD token auth, throttled async
chat completions, and a small CLI for local smoke testing.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

import aiolimiter
import openai
from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    DefaultAzureCredential,
    get_bearer_token_provider,
)
from openai.types.chat.chat_completion import ChatCompletion
from tenacity import (
    AsyncRetrying,
    Retrying,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)
from tqdm.asyncio import tqdm_asyncio

LOG = logging.getLogger(__name__)

API_VERSION = "2025-03-01-preview"
DEFAULT_ENDPOINT_NAME = "trapi-msrhf-shared"
ENDPOINTS: dict[str, str] = {
    "hanover-openai": "https://hanover-openai.openai.azure.com/",
    "hanover-openai-south": "https://hanover-openai-south.openai.azure.com/",
    "hanover-openai-east": "https://hanover-openai-eastus2.openai.azure.com/",
    "hanover-openai-west": "https://hanover-openai-westus.openai.azure.com/",
    "gcrgpt4aoai9spot": "https://gcrgpt4aoai9spot.openai.azure.com/",
    "gcraoai9sw1": "https://gcraoai9sw1.openai.azure.com/",
    "trapi-gcr-shared": "https://trapi.research.microsoft.com/gcr/shared",
    "trapi-msrhf-shared": "https://trapi.research.microsoft.com/msrhf/shared",
    "trapi-msrai4s-shared": "https://trapi.research.microsoft.com/msrai4s/shared",
}


def _build_credential_chain() -> ChainedTokenCredential:
    return ChainedTokenCredential(
        AzureCliCredential(),
        DefaultAzureCredential(
            exclude_cli_credential=True,
            exclude_environment_credential=True,
            exclude_shared_token_cache_credential=True,
            exclude_developer_cli_credential=True,
            exclude_powershell_credential=True,
            exclude_interactive_browser_credential=True,
            exclude_visual_studio_code_credentials=True,
            managed_identity_client_id=os.environ.get("DEFAULT_IDENTITY_CLIENT_ID"),
        ),
    )


def _resolve_endpoint_name_url(
    endpoint_name: str | None,
    endpoint_url: str | None,
) -> tuple[str, str]:
    if endpoint_url:
        return "custom", endpoint_url

    name = endpoint_name or DEFAULT_ENDPOINT_NAME
    url = ENDPOINTS.get(name)
    if url is None:
        available = sorted(ENDPOINTS)
        raise ValueError(f"Unknown endpoint name {name!r}. Available endpoints: {available}")
    return name, url


def _default_api_key_for_endpoint(endpoint_name: str) -> str | None:
    if endpoint_name == "gcrgpt4aoai9spot":
        return os.environ.get("AZURE_OPENAI_API_KEY")
    return None


def resolve_endpoint_config(
    *,
    model: str,
    endpoint_name: str | None = None,
    endpoint: str | None = None,
    api_key: str | None = None,
) -> tuple[str, str, Any | None, str | None]:
    resolved_name, target_endpoint = _resolve_endpoint_name_url(endpoint_name, endpoint)
    resolved_api_key = api_key or _default_api_key_for_endpoint(resolved_name)
    target_deployment = model

    if resolved_api_key:
        return target_endpoint, target_deployment, None, resolved_api_key

    scope = (
        "api://trapi/.default"
        if target_endpoint.startswith("https://trapi.research.microsoft.com")
        else "https://cognitiveservices.azure.com/.default"
    )
    token_provider = get_bearer_token_provider(_build_credential_chain(), scope)
    return target_endpoint, target_deployment, token_provider, None


def _normalize_chat_kwargs(model: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(kwargs)
    if model.startswith("o") and "max_tokens" in normalized:
        normalized.setdefault("max_completion_tokens", normalized.pop("max_tokens"))
    return normalized


def _is_retryable_openai_error(exc: BaseException) -> bool:
    if isinstance(
        exc,
        (
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
            openai.InternalServerError,
        ),
    ):
        return True
    if isinstance(exc, openai.APIStatusError):
        status_code = exc.status_code or 0
        return status_code == 429 or status_code >= 500
    return False


def run_direct_chat_completion(
    *,
    model: str,
    messages: list[dict[str, Any]],
    api_version: str = API_VERSION,
    endpoint_name: str | None = None,
    endpoint: str | None = None,
    api_key: str | None = None,
    retry_attempts: int = 3,
    **kwargs: Any,
) -> ChatCompletion:
    """Run a single direct Azure OpenAI chat completion request.

    Endpoint resolution order:
    1) explicit `endpoint`
    2) named `endpoint_name` from ENDPOINTS
    3) default endpoint name
    """
    target_endpoint, target_deployment, token_provider, resolved_api_key = (
        resolve_endpoint_config(
            model=model,
            endpoint_name=endpoint_name,
            endpoint=endpoint,
            api_key=api_key,
        )
    )
    request_kwargs = _normalize_chat_kwargs(model=model, kwargs=kwargs)

    if resolved_api_key:
        client = openai.AzureOpenAI(
            azure_endpoint=target_endpoint,
            api_version=api_version,
            api_key=resolved_api_key,
        )
    else:
        client = openai.AzureOpenAI(
            azure_endpoint=target_endpoint,
            api_version=api_version,
            azure_ad_token_provider=token_provider,
        )

    retry_policy = Retrying(
        stop=stop_after_attempt(retry_attempts),
        wait=wait_exponential_jitter(initial=1, max=20),
        retry=retry_if_exception(_is_retryable_openai_error),
        before_sleep=before_sleep_log(LOG, logging.WARNING),
        reraise=True,
    )
    try:
        for attempt in retry_policy:
            with attempt:
                return client.chat.completions.create(
                    model=target_deployment,
                    messages=messages,
                    **request_kwargs,
                )
        raise RuntimeError("Unexpected retry flow termination for direct chat completion.")
    finally:
        client.close()


def _encode_local_image_path(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "png"
    payload = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{suffix};base64,{payload}"


async def _load_local_images_in_messages(messages: list[dict[str, Any]]) -> None:
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "image_url":
                continue

            image_url = part.get("image_url")
            if isinstance(image_url, str):
                path = Path(image_url)
                if path.exists():
                    part["image_url"] = {"url": _encode_local_image_path(path)}
                continue

            if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
                url = image_url["url"]
                path = Path(url)
                if path.exists():
                    part["image_url"] = {"url": _encode_local_image_path(path)}


async def _throttled_chat_completion_create(
    *,
    client: openai.AsyncAzureOpenAI,
    model: str,
    messages: list[dict[str, Any]],
    limiter: aiolimiter.AsyncLimiter,
    retries: int = 3,
    **kwargs: Any,
) -> ChatCompletion | None:
    async with limiter:
        await _load_local_images_in_messages(messages)
        request_kwargs = _normalize_chat_kwargs(model=model, kwargs=kwargs)
        retry_policy = AsyncRetrying(
            stop=stop_after_attempt(retries),
            wait=wait_exponential_jitter(initial=1, max=20),
            retry=retry_if_exception(_is_retryable_openai_error),
            before_sleep=before_sleep_log(LOG, logging.WARNING),
            reraise=True,
        )
        try:
            async for attempt in retry_policy:
                with attempt:
                    return await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        **request_kwargs,
                    )
        except Exception as exc:  # noqa: BLE001
            LOG.error("Chat completion failed after retries: %s", exc)
            return None

    return None


async def generate_from_openai_chat_completion(
    *,
    batch_messages: list[list[dict[str, Any]]],
    model: str,
    endpoint_name: str | None = None,
    endpoint: str | None = None,
    api_key: str | None = None,
    requests_per_minute: int = 150,
    api_version: str = API_VERSION,
    **kwargs: Any,
) -> list[ChatCompletion | None]:
    target_endpoint, deployment_name, token_provider, resolved_api_key = (
        resolve_endpoint_config(
            model=model,
            endpoint_name=endpoint_name,
            endpoint=endpoint,
            api_key=api_key,
        )
    )
    if resolved_api_key:
        client = openai.AsyncAzureOpenAI(
            azure_endpoint=target_endpoint,
            api_version=api_version,
            api_key=resolved_api_key,
        )
    else:
        client = openai.AsyncAzureOpenAI(
            azure_endpoint=target_endpoint,
            api_version=api_version,
            azure_ad_token_provider=token_provider,
        )
    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    jobs = [
        _throttled_chat_completion_create(
            client=client,
            model=deployment_name,
            messages=messages,
            limiter=limiter,
            **kwargs,
        )
        for messages in batch_messages
    ]
    responses = await tqdm_asyncio.gather(*jobs)
    await client.close()
    return responses


def run_batch_chat_completion(
    *,
    all_messages: list[list[dict[str, Any]]],
    batch_size: int,
    retry: int = 10,
    model: str,
    endpoint_name: str | None = None,
    endpoint: str | None = None,
    api_key: str | None = None,
    requests_per_minute: int = 150,
    api_version: str = API_VERSION,
    **kwargs: Any,
) -> list[ChatCompletion | None]:
    pending_ids = list(range(len(all_messages)))
    all_responses: list[ChatCompletion | None] = [None] * len(all_messages)

    for run_index in range(1, retry + 1):
        pending_ids = [i for i in pending_ids if all_responses[i] is None]
        if not pending_ids:
            break

        LOG.info("Run %s/%s: %s pending requests", run_index, retry, len(pending_ids))

        for offset in range(0, len(pending_ids), batch_size):
            batch_ids = pending_ids[offset : offset + batch_size]
            batch_messages = [all_messages[item_id] for item_id in batch_ids]
            batch_responses = asyncio.run(
                generate_from_openai_chat_completion(
                    batch_messages=batch_messages,
                    model=model,
                    endpoint_name=endpoint_name,
                    endpoint=endpoint,
                    api_key=api_key,
                    requests_per_minute=requests_per_minute,
                    api_version=api_version,
                    **kwargs,
                )
            )
            for item_id, response in zip(batch_ids, batch_responses):
                all_responses[item_id] = response

    return all_responses


def call_openai_api(
    *,
    pmids: list[str],
    all_messages: list[list[dict[str, Any]]],
    model: str,
    cache: str | Path | None = None,
) -> list[dict[str, Any]]:
    all_results: list[dict[str, Any]] = []
    cache_pmids: set[str] = set()
    cache_path = Path(cache) if cache else None

    if cache_path and cache_path.exists():
        for line in cache_path.read_text().splitlines():
            result = json.loads(line)
            pmid = result["pmid"]
            if pmid in pmids:
                cache_pmids.add(pmid)
                response = ChatCompletion.construct(**result["response"])
                all_results.append({"pmid": pmid, "response": response})

    todo_items = [
        (pmid, msg) for pmid, msg in zip(pmids, all_messages) if pmid not in cache_pmids
    ]
    todo_pmids = [pmid for pmid, _ in todo_items]
    todo_messages = [msg for _, msg in todo_items]

    if todo_pmids:
        kwargs: dict[str, Any] = {
            "all_messages": todo_messages,
            "batch_size": 128,
            "model": model,
        }
        if model.startswith("o") and not model.startswith("openai"):
            kwargs["reasoning_effort"] = "medium"

        all_responses = run_batch_chat_completion(**kwargs)
        for pmid, response in zip(todo_pmids, all_responses):
            all_results.append({"pmid": pmid, "response": response})

        if cache_path is not None:
            with cache_path.open("a", encoding="utf-8") as handle:
                for pmid, response in zip(todo_pmids, all_responses):
                    if response is None:
                        continue
                    payload = {"pmid": pmid, "response": response.to_dict()}
                    handle.write(json.dumps(payload) + "\n")

    ordered = {pmid: idx for idx, pmid in enumerate(pmids)}
    return sorted(all_results, key=lambda item: ordered[item["pmid"]])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test internal Azure OpenAI endpoint calls."
    )
    parser.add_argument(
        "--example",
        choices=["batch", "direct"],
        default="batch",
        help="Which example flow to run.",
    )
    parser.add_argument("--model", default="o3", help="Model alias in endpoint mapping.")
    parser.add_argument(
        "--endpoint-name",
        choices=sorted(ENDPOINTS),
        default=None,
        help="Named endpoint from the internal ENDPOINTS map.",
    )
    parser.add_argument(
        "--connection",
        dest="endpoint_name",
        choices=sorted(ENDPOINTS),
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--prompt",
        action="append",
        help="Prompt to send (repeat for multiple requests).",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--requests-per-minute", type=int, default=150)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument(
        "--tool-json",
        action="append",
        default=None,
        help=(
            "Raw JSON tool spec. Can be either a full tool object "
            "({'type':'function','function':{...}}) or a function object ({...}). "
            "Repeat for multiple tools."
        ),
    )
    parser.add_argument(
        "--function-name",
        default=None,
        help="Convenience flag to define a function tool name from CLI.",
    )
    parser.add_argument(
        "--function-description",
        default=None,
        help="Convenience flag to define a function tool description from CLI.",
    )
    parser.add_argument(
        "--function-parameters-json",
        default=None,
        help=(
            "JSON schema for the function parameters, e.g. "
            '\'{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}\'.'
        ),
    )
    parser.add_argument(
        "--tool-choice",
        default=None,
        help=(
            "Tool selection mode: auto|none|required, "
            "function:<name>, or raw JSON object."
        ),
    )
    parser.add_argument(
        "--parallel-tool-calls",
        choices=["true", "false"],
        default=None,
        help="Whether to allow parallel tool calls.",
    )
    parser.add_argument(
        "--azure-endpoint",
        default=None,
        help="Optional endpoint override for direct or batch mode.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional API key (if omitted, Entra ID token auth is used).",
    )
    parser.add_argument(
        "--api-version",
        default=API_VERSION,
        help="Azure OpenAI API version.",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=["low", "medium", "high"],
        default=None,
        help="Only used for o-series models.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args()


def _parse_tool_choice(value: str | None) -> str | dict[str, Any] | None:
    if value is None:
        return None
    if value in {"auto", "none", "required"}:
        return value
    if value.startswith("function:"):
        name = value.split(":", 1)[1].strip()
        if not name:
            raise ValueError("Invalid --tool-choice. Expected function:<name>.")
        return {"type": "function", "function": {"name": name}}
    return json.loads(value)


def _normalize_tool_json(raw_tool: str) -> dict[str, Any]:
    parsed = json.loads(raw_tool)
    if isinstance(parsed, dict) and parsed.get("type") == "function":
        return parsed
    if isinstance(parsed, dict) and "name" in parsed:
        return {"type": "function", "function": parsed}
    raise ValueError(
        "Invalid --tool-json payload. Provide a full tool object or function object."
    )


def _build_function_calling_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    tools: list[dict[str, Any]] = []

    if args.tool_json:
        tools.extend(_normalize_tool_json(raw_tool) for raw_tool in args.tool_json)

    if args.function_name:
        function_payload: dict[str, Any] = {"name": args.function_name}
        if args.function_description is not None:
            function_payload["description"] = args.function_description
        if args.function_parameters_json is not None:
            function_payload["parameters"] = json.loads(args.function_parameters_json)
        tools.append({"type": "function", "function": function_payload})

    if tools:
        kwargs["tools"] = tools

    tool_choice = _parse_tool_choice(args.tool_choice)
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice

    if args.parallel_tool_calls is not None:
        kwargs["parallel_tool_calls"] = args.parallel_tool_calls == "true"

    return kwargs


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))

    prompts = args.prompt or [
        "Write a short poem about asynchronous execution.",
        "List three practical use-cases for SQL query planners.",
    ]
    all_messages = [[{"role": "user", "content": prompt}] for prompt in prompts]

    kwargs: dict[str, Any] = {}
    if args.reasoning_effort is not None and args.model.startswith("o"):
        kwargs["reasoning_effort"] = args.reasoning_effort
    if args.temperature is not None:
        kwargs["temperature"] = args.temperature
    if args.max_tokens is not None:
        kwargs["max_tokens"] = args.max_tokens
    kwargs.update(_build_function_calling_kwargs(args))

    if args.example == "batch":
        batch_kwargs: dict[str, Any] = {
            "all_messages": all_messages,
            "batch_size": args.batch_size,
            "model": args.model,
            "endpoint_name": args.endpoint_name,
            "endpoint": args.azure_endpoint,
            "api_key": args.api_key,
            "requests_per_minute": args.requests_per_minute,
            "api_version": args.api_version,
            **kwargs,
        }
        responses = run_batch_chat_completion(**batch_kwargs)
        serializable = [resp.to_dict() if resp is not None else None for resp in responses]
        print(json.dumps(serializable, indent=2))
        return

    direct_response = run_direct_chat_completion(
        model=args.model,
        messages=all_messages[0],
        endpoint_name=args.endpoint_name,
        endpoint=args.azure_endpoint,
        api_key=args.api_key,
        api_version=args.api_version,
        **kwargs,
    )
    print(json.dumps(direct_response.to_dict(), indent=2))


if __name__ == "__main__":
    main()
