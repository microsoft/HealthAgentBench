import json

from ehr_co_scientist.tools.catalog import (
    TOOL_DEFINITIONS,
    TOOL_REGISTRY,
    should_stop_on_call_in_evaluation,
)
from ehr_co_scientist.tools.tooling.function_tools import (
    call_registered_tool,
    get_openai_function_tools,
    write_openai_function_tools_json,
)
from ehr_co_scientist.tools.tooling.runtime import ToolRuntime


class _FakeFHIRClient:
    def __init__(self):
        self.calls = []

    def search(self, resource_type, params):
        self.calls.append(("search", resource_type, dict(params)))
        return {"resourceType": "Bundle", "type": "searchset"}

    def create(self, resource_type, resource_body):
        self.calls.append(("create", resource_type, dict(resource_body)))
        return {"resourceType": resource_type, "id": "example"}


def test_get_openai_function_tools_contains_all_registry_tools():
    tools = get_openai_function_tools(TOOL_DEFINITIONS)
    exported_names = {tool["function"]["name"] for tool in tools}
    assert exported_names == set(TOOL_REGISTRY)


def test_write_openai_function_tools_json_writes_tools_wrapper(tmp_path):
    output = tmp_path / "fhir_tools.json"
    write_openai_function_tools_json(
        output,
        tool_definitions=TOOL_DEFINITIONS,
        tool_names=["patient_search"],
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert "tools" in payload
    assert payload["tools"][0]["function"]["name"] == "patient_search"


def test_call_tool_dispatches_by_canonical_name():
    client = _FakeFHIRClient()
    result = call_registered_tool(
        "patient_search",
        ToolRuntime(fhir=client),
        registry=TOOL_REGISTRY,
        kwargs={"family": "Alice"},
    )
    assert result["resourceType"] == "Bundle"
    assert client.calls == [("search", "Patient", {"family": "Alice"})]


def test_patient_search_splits_full_name_to_family_given():
    client = _FakeFHIRClient()
    _ = call_registered_tool(
        "patient_search",
        ToolRuntime(fhir=client),
        registry=TOOL_REGISTRY,
        kwargs={"name": "Peter Stafford", "birthdate": "1932-12-29"},
    )
    assert client.calls == [
        (
            "search",
            "Patient",
            {"given": "Peter", "family": "Stafford", "birthdate": "1932-12-29"},
        )
    ]


def test_search_tool_required_fields_align_with_medagentbench():
    tools = {
        tool["function"]["name"]: tool["function"]["parameters"]
        for tool in get_openai_function_tools(TOOL_DEFINITIONS)
    }
    assert tools["condition_search"].get("required") == ["patient"]
    assert tools["lab_search"].get("required") == ["patient", "code"]
    assert tools["vital_search"].get("required") == ["patient"]
    assert tools["medicationrequest_search"].get("required") == ["patient"]
    assert tools["procedure_search"].get("required") == ["patient", "date"]


def test_create_tool_schemas_are_resource_specific():
    tools = {
        tool["function"]["name"]: tool["function"]["parameters"]
        for tool in get_openai_function_tools(TOOL_DEFINITIONS)
    }

    vital_required = tools["vital_create"]["properties"]["resource"]["required"]
    med_required = tools["medicationrequest_create"]["properties"]["resource"]["required"]
    procedure_required = tools["procedure_create"]["properties"]["resource"]["required"]

    assert vital_required == [
        "resourceType",
        "category",
        "code",
        "effectiveDateTime",
        "status",
        "valueString",
        "subject",
    ]
    assert med_required == [
        "resourceType",
        "medicationCodeableConcept",
        "authoredOn",
        "dosageInstruction",
        "status",
        "intent",
        "subject",
    ]
    assert procedure_required == [
        "resourceType",
        "code",
        "authoredOn",
        "status",
        "intent",
        "priority",
        "subject",
    ]


def test_procedure_create_posts_service_request():
    client = _FakeFHIRClient()
    payload = {"resourceType": "ServiceRequest", "status": "active"}
    _ = call_registered_tool(
        "procedure_create",
        ToolRuntime(fhir=client),
        registry=TOOL_REGISTRY,
        kwargs={"resource": payload},
    )
    assert client.calls == [("create", "ServiceRequest", payload)]


def test_write_tools_stop_in_evaluation_mode():
    assert should_stop_on_call_in_evaluation("vital_create") is True
    assert should_stop_on_call_in_evaluation("procedure_create") is True
    assert should_stop_on_call_in_evaluation("medicationrequest_create") is True
    assert should_stop_on_call_in_evaluation("patient_search") is False
