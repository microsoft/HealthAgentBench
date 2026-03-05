"""MedAgentBench-specific adapter over generic FHIR tools."""

from ehr_co_scientist.tools.fhir_tools import (  # noqa: F401
    FUNCTION_NAME_TO_TOOL_NAME,
    TOOL_DEFINITIONS,
    TOOL_REGISTRY,
    condition_search,
    lab_search,
    medicationrequest_create,
    medicationrequest_search,
    patient_search,
    procedure_create,
    procedure_search,
    vital_create,
)
