"""Reusable FHIR tool wrappers, client, and function-calling schemas."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ehr_co_scientist.tools.tooling import (
    ToolDefinition,
    build_function_name_alias,
    build_handler_registry,
    call_registered_tool,
    get_openai_function_tools as build_openai_function_tools,
    resolve_tool_name as resolve_registered_tool_name,
    write_openai_function_tools_json as write_function_tools_json,
)
from ehr_co_scientist.utils.http import JsonHttpClient


@dataclass
class FHIRClient:
    base_url: str
    timeout_s: float = 30.0
    _http: JsonHttpClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self._http = JsonHttpClient(timeout_s=self.timeout_s)

    def capability_statement(self) -> dict[str, Any]:
        return self._http.request_json(
            method="GET",
            url=f"{self.base_url}/metadata",
            headers={"Accept": "application/fhir+json"},
        )

    def search(self, resource_type: str, params: dict[str, str]) -> dict[str, Any]:
        return self._http.request_json(
            method="GET",
            url=f"{self.base_url}/{resource_type}",
            params=params,
            headers={"Accept": "application/fhir+json"},
        )

    def create(
        self, resource_type: str, resource_body: dict[str, Any]
    ) -> dict[str, Any]:
        return self._http.request_json(
            method="POST",
            url=f"{self.base_url}/{resource_type}",
            json_body=resource_body,
            headers={
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
        )


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
    # MedAgentBench maps this action tool to ServiceRequest.Create.
    return client.create("ServiceRequest", resource)


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


def _vital_create_resource_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "resourceType": {
                "type": "string",
                "description": 'Use "Observation" for vitals observations.',
            },
            "category": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "coding": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "system": {"type": "string"},
                                    "code": {"type": "string"},
                                    "display": {"type": "string"},
                                },
                            },
                        }
                    },
                },
            },
            "code": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "What is being measured.",
                    }
                },
            },
            "effectiveDateTime": {"type": "string"},
            "status": {"type": "string"},
            "valueString": {"type": "string"},
            "subject": {
                "type": "object",
                "properties": {"reference": {"type": "string"}},
            },
        },
        "required": [
            "resourceType",
            "category",
            "code",
            "effectiveDateTime",
            "status",
            "valueString",
            "subject",
        ],
    }


def _medicationrequest_create_resource_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "resourceType": {"type": "string"},
            "medicationCodeableConcept": {
                "type": "object",
                "properties": {
                    "coding": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "system": {"type": "string"},
                                "code": {"type": "string"},
                                "display": {"type": "string"},
                            },
                        },
                    },
                    "text": {"type": "string"},
                },
            },
            "authoredOn": {"type": "string"},
            "dosageInstruction": {
                "type": "array",
                "items": {"type": "object"},
            },
            "status": {"type": "string"},
            "intent": {"type": "string"},
            "subject": {
                "type": "object",
                "properties": {"reference": {"type": "string"}},
            },
        },
        "required": [
            "resourceType",
            "medicationCodeableConcept",
            "authoredOn",
            "dosageInstruction",
            "status",
            "intent",
            "subject",
        ],
    }


def _servicerequest_create_resource_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "resourceType": {"type": "string"},
            "code": {
                "type": "object",
                "properties": {
                    "coding": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "system": {"type": "string"},
                                "code": {"type": "string"},
                                "display": {"type": "string"},
                            },
                        },
                    }
                },
            },
            "authoredOn": {"type": "string"},
            "status": {"type": "string"},
            "intent": {"type": "string"},
            "priority": {"type": "string"},
            "subject": {
                "type": "object",
                "properties": {"reference": {"type": "string"}},
            },
            "note": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
            },
            "occurrenceDateTime": {"type": "string"},
        },
        "required": [
            "resourceType",
            "code",
            "authoredOn",
            "status",
            "intent",
            "priority",
            "subject",
        ],
    }


def _wrap_resource_schema(resource_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {"resource": resource_schema},
        "required": ["resource"],
        "additionalProperties": False,
    }


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
        parameters=_wrap_resource_schema(_vital_create_resource_schema()),
        handler=vital_create,
    ),
    "procedure.create": ToolDefinition(
        tool_name="procedure.create",
        function_name="procedure_create",
        description="Create a new ServiceRequest resource.",
        parameters=_wrap_resource_schema(_servicerequest_create_resource_schema()),
        handler=procedure_create,
    ),
    "medicationrequest.create": ToolDefinition(
        tool_name="medicationrequest.create",
        function_name="medicationrequest_create",
        description="Create a new MedicationRequest resource.",
        parameters=_wrap_resource_schema(_medicationrequest_create_resource_schema()),
        handler=medicationrequest_create,
    ),
}

TOOL_REGISTRY = build_handler_registry(TOOL_DEFINITIONS)
FUNCTION_NAME_TO_TOOL_NAME = build_function_name_alias(TOOL_DEFINITIONS)


# Backward-compatible convenience wrappers that bind generic tooling helpers
# to the FHIR toolset for existing call sites.
def resolve_tool_name(name: str) -> str:
    return resolve_registered_tool_name(
        name,
        registry=TOOL_REGISTRY,
        function_name_to_tool_name=FUNCTION_NAME_TO_TOOL_NAME,
    )


def get_openai_function_tools(tool_names: list[str] | None = None) -> list[dict[str, Any]]:
    return build_openai_function_tools(TOOL_DEFINITIONS, tool_names)


def write_openai_function_tools_json(
    output_path: str | Path,
    *,
    tool_names: list[str] | None = None,
    wrap_with_tools_key: bool = True,
) -> Path:
    return write_function_tools_json(
        output_path,
        tool_definitions=TOOL_DEFINITIONS,
        tool_names=tool_names,
        wrap_with_tools_key=wrap_with_tools_key,
    )


def call_tool(tool_name: str, client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    return call_registered_tool(
        tool_name,
        client,
        registry=TOOL_REGISTRY,
        function_name_to_tool_name=FUNCTION_NAME_TO_TOOL_NAME,
        kwargs=kwargs,
    )


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
