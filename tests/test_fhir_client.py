from ehr_co_scientist.tools.fhir_tools import FHIRClient


class _FakeHttp:
    def __init__(self):
        self.calls = []

    def request_json(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["method"] == "GET" and kwargs["url"].endswith("/metadata"):
            return {"resourceType": "CapabilityStatement"}
        return {"ok": True, "echo": kwargs}


def test_fhir_client_capability_search_create():
    client = FHIRClient(base_url="http://localhost:8080")
    fake = _FakeHttp()
    client._http = fake  # type: ignore[attr-defined]

    cap = client.capability_statement()
    assert cap["resourceType"] == "CapabilityStatement"

    search = client.search("Patient", {"name": "Alice"})
    assert search["ok"] is True

    created = client.create("Observation", {"resourceType": "Observation"})
    assert created["ok"] is True

    assert len(fake.calls) == 3
    assert fake.calls[1]["url"].endswith("/Patient")
    assert fake.calls[2]["method"] == "POST"
