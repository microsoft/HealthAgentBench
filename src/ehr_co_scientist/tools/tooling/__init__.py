"""Shared, tool-agnostic helpers for tool schemas/registry/dispatch."""

from .function_tools import (
    ToolDefinition,
    build_function_name_alias,
    build_handler_registry,
    call_registered_tool,
    get_openai_function_tools,
    resolve_tool_name,
    write_openai_function_tools_json,
)

__all__ = [
    "ToolDefinition",
    "build_function_name_alias",
    "build_handler_registry",
    "call_registered_tool",
    "get_openai_function_tools",
    "resolve_tool_name",
    "write_openai_function_tools_json",
]

