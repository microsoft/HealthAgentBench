"""FHIR HTTP client abstraction for MedAgentBench-aligned workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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

    def create(self, resource_type: str, resource_body: dict[str, Any]) -> dict[str, Any]:
        return self._http.request_json(
            method="POST",
            url=f"{self.base_url}/{resource_type}",
            json_body=resource_body,
            headers={
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
        )
