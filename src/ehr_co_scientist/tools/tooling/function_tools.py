"""Tool-agnostic helpers for tool registry, dispatch, and OpenAI export."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .runtime import ToolRuntime


@dataclass(frozen=True)
class ToolDefinition:
    tool_name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., dict[str, Any]]
    stop_on_call_in_evaluation: bool = False


_PENDING_REGISTRATIONS: list[dict[str, Any]] = []
_REGISTERED_TOOL_NAMES: set[str] = set()


def register_tool(
    *,
    tool_name: str,
    description: str,
    parameters: dict[str, Any] | Callable[[], dict[str, Any]],
    stop_on_call_in_evaluation: bool = False,
):
    """Decorator to register a tool handler for catalog materialization."""

    def _decorator(fn: Callable[..., dict[str, Any]]):
        if tool_name in _REGISTERED_TOOL_NAMES:
            raise ValueError(f"Duplicate tool_name registration: {tool_name}")
        _REGISTERED_TOOL_NAMES.add(tool_name)
        _PENDING_REGISTRATIONS.append(
            {
                "tool_name": tool_name,
                "description": description,
                "parameters": parameters,
                "handler": fn,
                "stop_on_call_in_evaluation": stop_on_call_in_evaluation,
            }
        )
        return fn

    return _decorator


def collect_registered_tool_definitions() -> dict[str, ToolDefinition]:
    definitions: dict[str, ToolDefinition] = {}
    for entry in _PENDING_REGISTRATIONS:
        raw_parameters = entry["parameters"]
        resolved_parameters = (
            raw_parameters() if callable(raw_parameters) else raw_parameters
        )
        definitions[entry["tool_name"]] = ToolDefinition(
            tool_name=entry["tool_name"],
            description=entry["description"],
            parameters=resolved_parameters,
            handler=entry["handler"],
            stop_on_call_in_evaluation=entry["stop_on_call_in_evaluation"],
        )
    return definitions


def build_handler_registry(
    tool_definitions: Mapping[str, ToolDefinition],
) -> dict[str, Callable[..., dict[str, Any]]]:
    return {name: definition.handler for name, definition in tool_definitions.items()}


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
                    "name": definition.tool_name,
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
    tool_runtime: ToolRuntime,
    *,
    registry: Mapping[str, Callable[..., dict[str, Any]]],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    try:
        fn = registry[tool_name]
    except KeyError as exc:  # noqa: PERF203
        available = ", ".join(sorted(registry))
        raise ValueError(f"Unknown tool name: {tool_name}. Available: {available}") from exc
    return fn(tool_runtime, **kwargs)
