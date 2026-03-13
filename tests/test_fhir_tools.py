import json

from medcli.tools.catalog import (
    TOOL_DEFINITIONS,
    TOOL_REGISTRY,
    should_pretend_on_call_in_evaluation,
)
from medcli.tools.tooling.function_tools import (
    call_registered_tool,
    get_openai_function_tools,
    write_openai_function_tools_json,
)
from medcli.tools.tooling.runtime import ToolRuntime


class _FakeFHIRClient:
    def __init__(self):
        self.calls = []

    def search(self, resource_type, params):
        self.calls.append(("search", resource_type, dict(params)))
        return {"resourceType": "Bundle", "type": "searchset"}

    def create(self, resource_type, resource_body):
        self.calls.append(("create", resource_type, dict(resource_body)))
        return {"resourceType": resource_type, "id": "example"}


EXPECTED_TOOL_NAMES = {
    "get_condition",
    "get_observation_labs",
    "get_observation_vitals",
    "post_observation_vitals",
    "get_medicationrequest",
    "post_medicationrequest",
    "get_procedure",
    "post_servicerequest",
    "get_patient",
}


def test_get_openai_function_tools_contains_all_registry_tools():
    tools = get_openai_function_tools(TOOL_DEFINITIONS)
    exported_names = {tool["function"]["name"] for tool in tools}
    assert exported_names == EXPECTED_TOOL_NAMES
    assert exported_names == set(TOOL_REGISTRY)


def test_write_openai_function_tools_json_writes_tools_wrapper(tmp_path):
    output = tmp_path / "fhir_tools.json"
    write_openai_function_tools_json(
        output,
        tool_definitions=TOOL_DEFINITIONS,
        tool_names=["get_patient"],
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert "tools" in payload
    assert payload["tools"][0]["function"]["name"] == "get_patient"


def test_call_tool_dispatches_get_patient_without_convenience_fallbacks():
    client = _FakeFHIRClient()
    result = call_registered_tool(
        "get_patient",
        ToolRuntime(fhir=client),
        registry=TOOL_REGISTRY,
        kwargs={"name": "Peter Stafford", "birthdate": "1932-12-29"},
    )
    assert result["resourceType"] == "Bundle"
    assert client.calls == [
        (
            "search",
            "Patient",
            {"name": "Peter Stafford", "birthdate": "1932-12-29"},
        )
    ]


def test_search_tool_required_fields_align_with_medagentbench():
    tools = {
        tool["function"]["name"]: tool["function"]["parameters"]
        for tool in get_openai_function_tools(TOOL_DEFINITIONS)
    }
    assert tools["get_condition"]["required"] == ["patient"]
    assert tools["get_observation_labs"]["required"] == ["code", "patient"]
    assert tools["get_observation_vitals"]["required"] == ["category", "patient"]
    assert tools["get_medicationrequest"]["required"] == ["patient"]
    assert tools["get_procedure"]["required"] == ["date", "patient"]
    assert tools["get_patient"]["required"] == []
    assert tools["get_condition"]["additionalProperties"] is False
    assert tools["get_observation_labs"]["additionalProperties"] is False


def test_create_tool_schemas_are_primitive_not_resource_wrapped():
    tools = {
        tool["function"]["name"]: tool["function"]["parameters"]
        for tool in get_openai_function_tools(TOOL_DEFINITIONS)
    }

    vital_required = tools["post_observation_vitals"]["required"]
    med_required = tools["post_medicationrequest"]["required"]
    service_required = tools["post_servicerequest"]["required"]

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
    assert service_required == [
        "resourceType",
        "code",
        "authoredOn",
        "status",
        "intent",
        "priority",
        "subject",
    ]
    assert "resource" not in tools["post_observation_vitals"]["properties"]


def test_post_servicerequest_posts_raw_payload():
    client = _FakeFHIRClient()
    payload = {"resourceType": "ServiceRequest", "status": "active"}
    _ = call_registered_tool(
        "post_servicerequest",
        ToolRuntime(fhir=client),
        registry=TOOL_REGISTRY,
        kwargs=payload,
    )
    assert client.calls == [("create", "ServiceRequest", payload)]


def test_write_tools_pretend_in_evaluation_mode():
    assert should_pretend_on_call_in_evaluation("post_observation_vitals") is True
    assert should_pretend_on_call_in_evaluation("post_servicerequest") is True
    assert should_pretend_on_call_in_evaluation("post_medicationrequest") is True
    assert should_pretend_on_call_in_evaluation("get_patient") is False
