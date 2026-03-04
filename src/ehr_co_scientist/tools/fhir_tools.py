"""Reusable FHIR tool wrappers for agent tool-calling flows."""

from __future__ import annotations

from typing import Any

from ehr_co_scientist.tools.fhir_client import FHIRClient


def _to_search_params(kwargs: dict[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in kwargs.items() if v is not None}


def patient_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    return client.search("Patient", _to_search_params(kwargs))


def lab_search(client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    params = _to_search_params(kwargs)
    params.setdefault("category", "laboratory")
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


TOOL_REGISTRY: dict[str, Any] = {
    "patient.search": patient_search,
    "lab.search": lab_search,
    "condition.search": condition_search,
    "procedure.search": procedure_search,
    "medicationrequest.search": medicationrequest_search,
    "vital.create": vital_create,
    "procedure.create": procedure_create,
    "medicationrequest.create": medicationrequest_create,
}


def call_tool(tool_name: str, client: FHIRClient, **kwargs: Any) -> dict[str, Any]:
    try:
        fn = TOOL_REGISTRY[tool_name]
    except KeyError as exc:  # noqa: PERF203
        available = ", ".join(sorted(TOOL_REGISTRY))
        raise ValueError(
            f"Unknown tool name: {tool_name}. Available: {available}"
        ) from exc

    return fn(client, **kwargs)
