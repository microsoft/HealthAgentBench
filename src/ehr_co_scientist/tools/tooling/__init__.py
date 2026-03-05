"""Shared, tool-agnostic helpers for tool schemas/registry/dispatch."""

from .function_tools import (
    ToolDefinition,
    build_handler_registry,
    call_registered_tool,
    collect_registered_tool_definitions,
    get_openai_function_tools,
    register_tool,
    write_openai_function_tools_json,
)

__all__ = [
    "ToolDefinition",
    "build_handler_registry",
    "call_registered_tool",
    "collect_registered_tool_definitions",
    "get_openai_function_tools",
    "register_tool",
    "write_openai_function_tools_json",
]
