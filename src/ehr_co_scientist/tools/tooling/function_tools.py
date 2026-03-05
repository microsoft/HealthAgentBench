"""Tool-agnostic helpers for tool registry, dispatch, and OpenAI export."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ToolDefinition:
    tool_name: str
    function_name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., dict[str, Any]]
    stop_on_call_in_evaluation: bool = False


def build_handler_registry(
    tool_definitions: Mapping[str, ToolDefinition],
) -> dict[str, Callable[..., dict[str, Any]]]:
    return {name: definition.handler for name, definition in tool_definitions.items()}


def build_function_name_alias(
    tool_definitions: Mapping[str, ToolDefinition],
) -> dict[str, str]:
    return {
        definition.function_name: name
        for name, definition in tool_definitions.items()
    }


def resolve_tool_name(
    name: str,
    *,
    registry: Mapping[str, Any],
    function_name_to_tool_name: Mapping[str, str],
) -> str:
    if name in registry:
        return name
    mapped = function_name_to_tool_name.get(name)
    if mapped is not None:
        return mapped
    return name


def get_openai_function_tools(
    tool_definitions: Mapping[str, ToolDefinition],
    tool_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    selected = tool_names or sorted(tool_definitions)
    tools: list[dict[str, Any]] = []
    for tool_name in selected:
        try:
            definition = tool_definitions[tool_name]
        except KeyError as exc:
            available = ", ".join(sorted(tool_definitions))
            raise ValueError(
                f"Unknown tool name for schema export: {tool_name}. Available: {available}"
            ) from exc
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": definition.function_name,
                    "description": definition.description,
                    "parameters": definition.parameters,
                },
            }
        )
    return tools


def write_openai_function_tools_json(
    output_path: str | Path,
    *,
    tool_definitions: Mapping[str, ToolDefinition],
    tool_names: list[str] | None = None,
    wrap_with_tools_key: bool = True,
) -> Path:
    path = Path(output_path)
    tools = get_openai_function_tools(tool_definitions, tool_names)
    payload: Any = {"tools": tools} if wrap_with_tools_key else tools
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def call_registered_tool(
    tool_name: str,
    client: Any,
    *,
    registry: Mapping[str, Callable[..., dict[str, Any]]],
    function_name_to_tool_name: Mapping[str, str],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    resolved_name = resolve_tool_name(
        tool_name,
        registry=registry,
        function_name_to_tool_name=function_name_to_tool_name,
    )
    try:
        fn = registry[resolved_name]
    except KeyError as exc:  # noqa: PERF203
        available_internal = ", ".join(sorted(registry))
        available_function = ", ".join(sorted(function_name_to_tool_name))
        raise ValueError(
            "Unknown tool name: "
            f"{tool_name}. Internal names: {available_internal}. "
            f"Function names: {available_function}"
        ) from exc
    return fn(client, **kwargs)
