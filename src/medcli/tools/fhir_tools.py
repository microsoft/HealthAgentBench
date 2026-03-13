"""Primitive MedAgentBench-aligned FHIR tools and schema export helpers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any

from medcli.tools.tooling import (
    ToolRuntime,
    register_tool,
    write_openai_function_tools_json,
)
from medcli.utils.http import JsonHttpClient


@dataclass
class FHIRClient:
    """Minimal FHIR REST client used by MedAgentBench-aligned tool handlers."""

    base_url: str
    timeout_s: float = 30.0
    _http: JsonHttpClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Normalize base URL and initialize shared HTTP transport."""
        self.base_url = self.base_url.rstrip("/")
        self._http = JsonHttpClient(timeout_s=self.timeout_s)

    def capability_statement(self) -> dict[str, Any]:
        """Fetch FHIR capability statement (`GET /metadata`)."""
        return self._http.request_json(
            method="GET",
            url=f"{self.base_url}/metadata",
            headers={"Accept": "application/fhir+json"},
        )

    def search(self, resource_type: str, params: dict[str, str]) -> dict[str, Any]:
        """Perform FHIR search (`GET /<Resource>?...`)."""
        return self._http.request_json(
            method="GET",
            url=f"{self.base_url}/{resource_type}",
            params=params,
            headers={"Accept": "application/fhir+json"},
        )

    def create(self, resource_type: str, resource_body: dict[str, Any]) -> dict[str, Any]:
        """Create FHIR resource (`POST /<Resource>`)."""
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
    return {key: str(value) for key, value in kwargs.items() if value is not None}


def _create_payload(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}


def _schema(
    properties: dict[str, Any],
    *,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


@register_tool(
    tool_name="get_condition",
    description=(
        "Condition.Search (Problems). Retrieve problems from a patient's chart. "
        "This resource is typically queried by patient and optionally category."
    ),
    parameters=lambda: _condition_parameters_schema(),
)
def get_condition(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Search Condition resources using the original MedAgentBench primitive schema."""
    return tool_runtime.require_fhir().search("Condition", _to_search_params(kwargs))


@register_tool(
    tool_name="get_observation_labs",
    description=(
        "Observation.Search (Labs). Retrieve laboratory observations by patient "
        "and code, with optional date filtering."
    ),
    parameters=lambda: _observation_labs_parameters_schema(),
)
def get_observation_labs(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Search Observation resources for lab-style queries."""
    return tool_runtime.require_fhir().search("Observation", _to_search_params(kwargs))


@register_tool(
    tool_name="get_observation_vitals",
    description=(
        "Observation.Search (Vitals). Retrieve vital signs and other non-duplicable "
        "flowsheet data by patient, category, and optional date."
    ),
    parameters=lambda: _observation_vitals_parameters_schema(),
)
def get_observation_vitals(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Search Observation resources for vital-sign queries."""
    return tool_runtime.require_fhir().search("Observation", _to_search_params(kwargs))


@register_tool(
    tool_name="post_observation_vitals",
    description=(
        "Observation.Create (Vitals). File a new vitals Observation payload "
        "to the FHIR server."
    ),
    parameters=lambda: _observation_create_parameters_schema(),
    pretend_on_call_in_evaluation=True,
)
def post_observation_vitals(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Create an Observation resource using the primitive MedAgentBench payload shape."""
    return tool_runtime.require_fhir().create("Observation", _create_payload(kwargs))


@register_tool(
    tool_name="get_medicationrequest",
    description=(
        "MedicationRequest.Search (Signed Medication Order). Query medication orders "
        "for a patient and optionally filter by category or date."
    ),
    parameters=lambda: _medicationrequest_search_parameters_schema(),
)
def get_medicationrequest(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Search MedicationRequest resources using the primitive MedAgentBench schema."""
    return tool_runtime.require_fhir().search("MedicationRequest", _to_search_params(kwargs))


@register_tool(
    tool_name="post_medicationrequest",
    description="MedicationRequest.Create.",
    parameters=lambda: _medicationrequest_create_parameters_schema(),
    pretend_on_call_in_evaluation=True,
)
def post_medicationrequest(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Create a MedicationRequest resource using the primitive MedAgentBench payload shape."""
    return tool_runtime.require_fhir().create("MedicationRequest", _create_payload(kwargs))


@register_tool(
    tool_name="get_procedure",
    description=(
        "Procedure.Search (Orders). Query procedures for a patient with required date "
        "filtering and optional code filtering."
    ),
    parameters=lambda: _procedure_search_parameters_schema(),
)
def get_procedure(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Search Procedure resources using the primitive MedAgentBench schema."""
    return tool_runtime.require_fhir().search("Procedure", _to_search_params(kwargs))


@register_tool(
    tool_name="post_servicerequest",
    description="ServiceRequest.Create.",
    parameters=lambda: _servicerequest_create_parameters_schema(),
    pretend_on_call_in_evaluation=True,
)
def post_servicerequest(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Create a ServiceRequest resource using the primitive MedAgentBench payload shape."""
    return tool_runtime.require_fhir().create("ServiceRequest", _create_payload(kwargs))


@register_tool(
    tool_name="get_patient",
    description=(
        "Patient.Search. Filter or search for patients based on demographic "
        "parameters and patient identifiers."
    ),
    parameters=lambda: _patient_parameters_schema(),
)
def get_patient(tool_runtime: ToolRuntime, **kwargs: Any) -> dict[str, Any]:
    """Search Patient resources without MedCLI-specific convenience transforms."""
    return tool_runtime.require_fhir().search("Patient", _to_search_params(kwargs))


def _condition_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "category": {
                "type": "string",
                "description": 'Always "problem-list-item" for this API.',
            },
            "patient": {
                "type": "string",
                "description": "Reference to a patient resource the condition is for.",
            },
        },
        required=["patient"],
    )


def _observation_labs_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "code": {
                "type": "string",
                "description": "The observation identifier (base name).",
            },
            "date": {
                "type": "string",
                "description": "Date when the specimen was obtained.",
            },
            "patient": {
                "type": "string",
                "description": "Reference to a patient resource the condition is for.",
            },
        },
        required=["code", "patient"],
    )


def _observation_vitals_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "category": {
                "type": "string",
                "description": 'Use "vital-signs" to search for vitals observations.',
            },
            "date": {
                "type": "string",
                "description": "The date range for when the observation was taken.",
            },
            "patient": {
                "type": "string",
                "description": "Reference to a patient resource the condition is for.",
            },
        },
        required=["category", "patient"],
    )


def _observation_create_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "resourceType": {
                "type": "string",
                'description': 'Use "Observation" for vitals observations.',
            },
            "category": {
                "type": "array",
                "items": _schema(
                    {
                        "coding": {
                            "type": "array",
                            "items": _schema(
                                {
                                    "system": {
                                        "type": "string",
                                        "description": 'Use "http://hl7.org/fhir/observation-category" ',
                                    },
                                    "code": {
                                        "type": "string",
                                        'description': 'Use "vital-signs" ',
                                    },
                                    "display": {
                                        "type": "string",
                                        'description': 'Use "Vital Signs" ',
                                    },
                                }
                            ),
                        }
                    }
                ),
            },
            "code": _schema(
                {
                    "text": {
                        "type": "string",
                        "description": (
                            "The flowsheet ID, encoded flowsheet ID, or LOINC codes to "
                            "flowsheet mapping. What is being measured."
                        ),
                    }
                }
            ),
            "effectiveDateTime": {
                "type": "string",
                "description": "The date and time the observation was taken, in ISO format.",
            },
            "status": {
                "type": "string",
                'description': 'The status of the observation. Only a value of "final" is supported.',
            },
            "valueString": {
                "type": "string",
                "description": "Measurement value",
            },
            "subject": _schema(
                {
                    "reference": {
                        "type": "string",
                        "description": "The patient FHIR ID for whom the observation is about.",
                    }
                }
            ),
        },
        required=[
            "resourceType",
            "category",
            "code",
            "effectiveDateTime",
            "status",
            "valueString",
            "subject",
        ],
    )


def _medicationrequest_search_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "category": {
                "type": "string",
                "description": "The category of medication orders to search for.",
            },
            "date": {
                "type": "string",
                "description": "The medication administration date.",
            },
            "patient": {
                "type": "string",
                "description": "The FHIR patient ID.",
            },
        },
        required=["patient"],
    )


def _medicationrequest_create_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "resourceType": {
                "type": "string",
                'description': 'Use "MedicationRequest" for medication requests.',
            },
            "medicationCodeableConcept": _schema(
                {
                    "coding": {
                        "type": "array",
                        "items": _schema(
                            {
                                "system": {
                                    "type": "string",
                                    'description': 'Coding system such as "http://hl7.org/fhir/sid/ndc" ',
                                },
                                "code": {
                                    "type": "string",
                                    "description": "The actual code",
                                },
                                "display": {
                                    "type": "string",
                                    "description": "Display name",
                                },
                            }
                        ),
                    },
                    "text": {
                        "type": "string",
                        "description": "The order display name of the medication, otherwise the record name.",
                    },
                }
            ),
            "authoredOn": {
                "type": "string",
                "description": "The date the prescription was written.",
            },
            "dosageInstruction": {
                "type": "array",
                "items": _schema(
                    {
                        "route": _schema(
                            {
                                "text": {
                                    "type": "string",
                                    "description": "The medication route.",
                                }
                            }
                        ),
                        "doseAndRate": {
                            "type": "array",
                            "items": _schema(
                                {
                                    "doseQuantity": _schema(
                                        {
                                            "value": {"type": "number"},
                                            "unit": {
                                                "type": "string",
                                                'description': 'unit for the dose such as "g" ',
                                            },
                                        }
                                    ),
                                    "rateQuantity": _schema(
                                        {
                                            "value": {"type": "number"},
                                            "unit": {
                                                "type": "string",
                                                'description': 'unit for the rate such as "h" ',
                                            },
                                        }
                                    ),
                                }
                            ),
                        },
                    }
                ),
            },
            "status": {
                "type": "string",
                "description": "The status of the medication request.",
            },
            "intent": {
                "type": "string",
                "description": "The intent of the medication request.",
            },
            "subject": _schema(
                {
                    "reference": {
                        "type": "string",
                        "description": "The patient FHIR ID for whom the medication request is about.",
                    }
                }
            ),
        },
        required=[
            "resourceType",
            "medicationCodeableConcept",
            "authoredOn",
            "dosageInstruction",
            "status",
            "intent",
            "subject",
        ],
    )


def _procedure_search_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "code": {
                "type": "string",
                "description": "Specific procedure code to search for.",
            },
            "date": {
                "type": "string",
                "description": "Procedure date filter.",
            },
            "patient": {
                "type": "string",
                "description": "The FHIR patient ID.",
            },
        },
        required=["date", "patient"],
    )


def _servicerequest_create_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "resourceType": {
                "type": "string",
                'description': 'Use "ServiceRequest" for service requests.',
            },
            "code": _schema(
                {
                    "coding": {
                        "type": "array",
                        "items": _schema(
                            {
                                "system": {
                                    "type": "string",
                                    "description": "Coding system such as SNOMED or LOINC.",
                                },
                                "code": {
                                    "type": "string",
                                    "description": "The actual code",
                                },
                                "display": {
                                    "type": "string",
                                    "description": "Display name",
                                },
                            }
                        ),
                    }
                }
            ),
            "authoredOn": {
                "type": "string",
                "description": "The date the service request was authored.",
            },
            "status": {
                "type": "string",
                "description": "The status of the service request.",
            },
            "intent": {
                "type": "string",
                "description": "The intent of the service request.",
            },
            "priority": {
                "type": "string",
                "description": "Priority of the service request.",
            },
            "subject": _schema(
                {
                    "reference": {
                        "type": "string",
                        "description": "The patient FHIR ID for whom the service request is about.",
                    }
                }
            ),
            "note": _schema({"text": {"type": "string", "description": "Free-text comment."}}),
            "occurrenceDateTime": {
                "type": "string",
                "description": "Requested occurrence date/time.",
            },
        },
        required=[
            "resourceType",
            "code",
            "authoredOn",
            "status",
            "intent",
            "priority",
            "subject",
        ],
    )


def _patient_parameters_schema() -> dict[str, Any]:
    return _schema(
        {
            "address": {"type": "string", "description": "Search by full address text."},
            "address-city": {"type": "string", "description": "Search by city."},
            "address-postalcode": {"type": "string", "description": "Search by postal code."},
            "address-state": {"type": "string", "description": "Search by state."},
            "birthdate": {"type": "string", "description": "Patient birth date."},
            "family": {"type": "string", "description": "Patient family name."},
            "gender": {"type": "string", "description": "Patient gender."},
            "given": {"type": "string", "description": "Patient given name."},
            "identifier": {"type": "string", "description": "Patient identifier or MRN."},
            "legal-sex": {"type": "string", "description": "Legal sex."},
            "name": {"type": "string", "description": "Full patient name."},
            "telecom": {"type": "string", "description": "Phone or telecom search string."},
        }
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export MedAgentBench-aligned FHIR tool schemas for function calling."
    )
    parser.add_argument("--output", required=True, help="Path to write tools JSON file.")
    parser.add_argument(
        "--tool",
        action="append",
        default=None,
        help="Canonical tool name to include (repeatable). Defaults to all tools.",
    )
    parser.add_argument(
        "--as-list",
        action="store_true",
        help="Write a raw tools list instead of {'tools': [...]} wrapper.",
    )
    return parser.parse_args()


def main() -> None:
    """Export tool schemas for backend/demo consumption."""
    from medcli.tools.catalog import TOOL_DEFINITIONS

    args = _parse_args()
    written = write_openai_function_tools_json(
        args.output,
        tool_definitions=TOOL_DEFINITIONS,
        tool_names=args.tool,
        wrap_with_tools_key=not args.as_list,
    )
    print(f"wrote tools JSON: {written}")


if __name__ == "__main__":
    main()
