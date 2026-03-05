"""Central tool catalog materialized from decorator registrations."""

from __future__ import annotations

from ehr_co_scientist.tools.tooling import (
    build_handler_registry,
    collect_registered_tool_definitions,
)

# Keep explicit imports here so registration side effects are visible and
# maintainable. Add additional tool modules in this block as the catalog grows.
import ehr_co_scientist.tools.fhir_tools  # noqa: F401

TOOL_DEFINITIONS = collect_registered_tool_definitions()
TOOL_REGISTRY = build_handler_registry(TOOL_DEFINITIONS)


def should_stop_on_call_in_evaluation(tool_name: str) -> bool:
    definition = TOOL_DEFINITIONS.get(tool_name)
    return bool(definition and definition.stop_on_call_in_evaluation)
