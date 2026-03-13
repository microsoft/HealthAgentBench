from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def _base_url() -> str:
    return os.environ.get("FHIR_BASE_URL", "http://fhir:8080/fhir").rstrip("/")


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _get_json(path: str) -> dict[str, Any]:
    url = f"{_base_url()}/{path.lstrip('/')}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _query_string(params: dict[str, str | None]) -> str:
    pairs = [f"{key}={urllib.parse.quote(value)}" for key, value in params.items() if value]
    pairs.append("_format=json")
    return "&".join(pairs)


def _get(resource: str, params: dict[str, str | None]) -> None:
    _print(_get_json(f"{resource}?{_query_string(params)}"))


def _load_payload(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("payload file must contain one JSON object")
    return payload


def _simulate_post(resource_type: str, payload_file: str) -> None:
    payload = _load_payload(payload_file)
    if payload.get("resourceType") != resource_type:
        raise SystemExit(
            f"payload resourceType mismatch: expected {resource_type}, got {payload.get('resourceType')}"
        )
    _print(
        {
            "status": "accepted_simulated",
            "resource_url": f"{_base_url()}/{resource_type}",
            "payload": payload,
            "message": "POST request accepted (simulated). Copy this payload into the task row's payload field and finish with the final answer.",
        }
    )
