"""Reusable FHIR tool wrappers and function-calling schemas."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ehr_co_scientist.tools.fhir_client import FHIRClient


def _to_search_params(kwargs: dict[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in kwargs.items() if v is not None}


def patient_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    params = _to_search_params(kwargs)
    # Compatibility fallback: if caller provides a full name string, derive
    # family/given fields to match MedAgentBench-style Patient search usage.
    if "name" in params and "family" not in params and "given" not in params:
        raw_name = params.pop("name").strip()
        parts = [part for part in raw_name.split() if part]
        if len(parts) >= 2:
            params["given"] = " ".join(parts[:-1])
            params["family"] = parts[-1]
        elif parts:
            params["family"] = parts[0]
    return client.search("Patient", params)


def lab_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    params = _to_search_params(kwargs)
    params.setdefault("category", "laboratory")
    return client.search("Observation", params)


def vital_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    params = _to_search_params(kwargs)
    params.setdefault("category", "vital-signs")
    return client.search("Observation", params)


def condition_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    return client.search("Condition", _to_search_params(kwargs))


def procedure_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    return client.search("Procedure", _to_search_params(kwargs))


def medicationrequest_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    return client.search("MedicationRequest", _to_search_params(kwargs))


def vital_create(client: FHIRClient, resource: dict[str, Any]) -> dict[str, Any]:
    return client.create("Observation", resource)


def procedure_create(client: FHIRClient, resource: dict[str, Any]) -> dict[str, Any]:
    return client.create("Procedure", resource)


def medicationrequest_create(
    client: FHIRClient, resource: dict[str, Any]
) -> dict[str, Any]:
    return client.create("MedicationRequest", resource)


def _patient_search_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "_id": {"type": "string"},
            "identifier": {"type": "string"},
            "family": {"type": "string"},
            "given": {"type": "string"},
            "birthdate": {"type": "string"},
            "gender": {"type": "string"},
            "_count": {"type": "string"},
        },
        "additionalProperties": False,
    }


def _condition_search_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "patient": {"type": "string"},
            "category": {"type": "string"},
        },
        "required": ["patient"],
        "additionalProperties": False,
    }


def _lab_search_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "patient": {"type": "string"},
            "code": {"type": "string"},
            "date": {"type": "string"},
        },
        "required": ["patient", "code"],
        "additionalProperties": False,
    }


def _vital_search_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "patient": {"type": "string"},
            "category": {
                "type": "string",
                "enum": ["vital-signs"],
            },
            "date": {"type": "string"},
        },
        "required": ["patient"],
        "additionalProperties": False,
    }


def _procedure_search_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "patient": {"type": "string"},
            "date": {"type": "string"},
            "code": {"type": "string"},
        },
        "required": ["patient", "date"],
        "additionalProperties": False,
    }


def _medicationrequest_search_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "patient": {"type": "string"},
            "category": {"type": "string"},
            "date": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["patient"],
        "additionalProperties": False,
    }


def _create_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "resource": {
                "type": "object",
                "description": "FHIR resource body to create.",
            }
        },
        "required": ["resource"],
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class ToolDefinition:
    tool_name: str
    function_name: str
    description: str
    parameters: dict[str, Any]
    handler: Any


TOOL_DEFINITIONS: dict[str, ToolDefinition] = {
    "patient.search": ToolDefinition(
        tool_name="patient.search",
        function_name="patient_search",
        description=(
            "Search Patient resources. Prefer family + given (+ optional birthdate) "
            "for person matching."
        ),
        parameters=_patient_search_parameters_schema(),
        handler=patient_search,
    ),
    "lab.search": ToolDefinition(
        tool_name="lab.search",
        function_name="lab_search",
        description=(
            "Search Observation resources for laboratory results. "
            "Defaults category=laboratory when category is omitted."
        ),
        parameters=_lab_search_parameters_schema(),
        handler=lab_search,
    ),
    "vital.search": ToolDefinition(
        tool_name="vital.search",
        function_name="vital_search",
        description=(
            "Search Observation resources for vital signs. "
            "Defaults category=vital-signs when category is omitted."
        ),
        parameters=_vital_search_parameters_schema(),
        handler=vital_search,
    ),
    "condition.search": ToolDefinition(
        tool_name="condition.search",
        function_name="condition_search",
        description="Search Condition resources by standard FHIR query params.",
        parameters=_condition_search_parameters_schema(),
        handler=condition_search,
    ),
    "procedure.search": ToolDefinition(
        tool_name="procedure.search",
        function_name="procedure_search",
        description="Search Procedure resources by standard FHIR query params.",
        parameters=_procedure_search_parameters_schema(),
        handler=procedure_search,
    ),
    "medicationrequest.search": ToolDefinition(
        tool_name="medicationrequest.search",
        function_name="medicationrequest_search",
        description=(
            "Search MedicationRequest resources by standard FHIR query params."
        ),
        parameters=_medicationrequest_search_parameters_schema(),
        handler=medicationrequest_search,
    ),
    "vital.create": ToolDefinition(
        tool_name="vital.create",
        function_name="vital_create",
        description="Create a new Observation resource (typically a vital sign).",
        parameters=_create_parameters_schema(),
        handler=vital_create,
    ),
    "procedure.create": ToolDefinition(
        tool_name="procedure.create",
        function_name="procedure_create",
        description="Create a new Procedure resource.",
        parameters=_create_parameters_schema(),
        handler=procedure_create,
    ),
    "medicationrequest.create": ToolDefinition(
        tool_name="medicationrequest.create",
        function_name="medicationrequest_create",
        description="Create a new MedicationRequest resource.",
        parameters=_create_parameters_schema(),
        handler=medicationrequest_create,
    ),
}

TOOL_REGISTRY: dict[str, Any] = {
    name: definition.handler for name, definition in TOOL_DEFINITIONS.items()
}

FUNCTION_NAME_TO_TOOL_NAME: dict[str, str] = {
    definition.function_name: name for name, definition in TOOL_DEFINITIONS.items()
}


def resolve_tool_name(name: str) -> str:
    if name in TOOL_REGISTRY:
        return name
    mapped = FUNCTION_NAME_TO_TOOL_NAME.get(name)
    if mapped is not None:
        return mapped
    return name


def get_openai_function_tools(tool_names: list[str] | None = None) -> list[dict[str, Any]]:
    selected = tool_names or sorted(TOOL_DEFINITIONS)
    tools: list[dict[str, Any]] = []
    for tool_name in selected:
        try:
            definition = TOOL_DEFINITIONS[tool_name]
        except KeyError as exc:
            available = ", ".join(sorted(TOOL_DEFINITIONS))
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
    tool_names: list[str] | None = None,
    wrap_with_tools_key: bool = True,
) -> Path:
    path = Path(output_path)
    tools = get_openai_function_tools(tool_names)
    payload: Any = {"tools": tools} if wrap_with_tools_key else tools
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def call_tool(tool_name: str, client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    resolved_name = resolve_tool_name(tool_name)
    try:
        fn = TOOL_REGISTRY[resolved_name]
    except KeyError as exc:  # noqa: PERF203
        available_internal = ", ".join(sorted(TOOL_REGISTRY))
        available_function = ", ".join(sorted(FUNCTION_NAME_TO_TOOL_NAME))
        raise ValueError(
            "Unknown tool name: "
            f"{tool_name}. Internal names: {available_internal}. "
            f"Function names: {available_function}"
        ) from exc
    return fn(client, **kwargs)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export FHIR tool schemas for GPT function calling."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write tools JSON file.",
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=None,
        help="Internal tool name to include (repeatable). Defaults to all tools.",
    )
    parser.add_argument(
        "--as-list",
        action="store_true",
        help="Write a raw tools list instead of {'tools': [...]} wrapper.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    written = write_openai_function_tools_json(
        args.output,
        tool_names=args.tool,
        wrap_with_tools_key=not args.as_list,
    )
    print(f"wrote tools JSON: {written}")


if __name__ == "__main__":
    main()
