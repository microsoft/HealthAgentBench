#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    patient_parser = subparsers.add_parser("get-patient")
    for name in (
        "address",
        "address-city",
        "address-postalcode",
        "address-state",
        "birthdate",
        "family",
        "gender",
        "given",
        "identifier",
        "legal-sex",
        "name",
        "telecom",
    ):
        patient_parser.add_argument(f"--{name}")

    condition_parser = subparsers.add_parser("get-condition")
    condition_parser.add_argument("--patient", required=True)
    condition_parser.add_argument("--category")

    labs_parser = subparsers.add_parser("get-observation-labs")
    labs_parser.add_argument("--patient", required=True)
    labs_parser.add_argument("--code", required=True)
    labs_parser.add_argument("--date")

    vitals_parser = subparsers.add_parser("get-observation-vitals")
    vitals_parser.add_argument("--patient", required=True)
    vitals_parser.add_argument("--category", required=True)
    vitals_parser.add_argument("--date")

    meds_parser = subparsers.add_parser("get-medicationrequest")
    meds_parser.add_argument("--patient", required=True)
    meds_parser.add_argument("--category")
    meds_parser.add_argument("--date")

    procedure_parser = subparsers.add_parser("get-procedure")
    procedure_parser.add_argument("--patient", required=True)
    procedure_parser.add_argument("--date", required=True)
    procedure_parser.add_argument("--code")

    obs_post = subparsers.add_parser("post-observation-vitals")
    obs_post.add_argument("--payload-file", required=True)

    med_post = subparsers.add_parser("post-medicationrequest")
    med_post.add_argument("--payload-file", required=True)

    svc_post = subparsers.add_parser("post-servicerequest")
    svc_post.add_argument("--payload-file", required=True)

    args = parser.parse_args()

    if args.command == "get-patient":
        _get(
            "Patient",
            {name: getattr(args, name.replace("-", "_")) for name in (
                "address",
                "address-city",
                "address-postalcode",
                "address-state",
                "birthdate",
                "family",
                "gender",
                "given",
                "identifier",
                "legal-sex",
                "name",
                "telecom",
            )},
        )
    elif args.command == "get-condition":
        _get("Condition", {"patient": args.patient, "category": args.category})
    elif args.command == "get-observation-labs":
        _get("Observation", {"patient": args.patient, "code": args.code, "date": args.date})
    elif args.command == "get-observation-vitals":
        _get("Observation", {"patient": args.patient, "category": args.category, "date": args.date})
    elif args.command == "get-medicationrequest":
        _get("MedicationRequest", {"patient": args.patient, "category": args.category, "date": args.date})
    elif args.command == "get-procedure":
        _get("Procedure", {"patient": args.patient, "date": args.date, "code": args.code})
    elif args.command == "post-observation-vitals":
        _simulate_post("Observation", args.payload_file)
    elif args.command == "post-medicationrequest":
        _simulate_post("MedicationRequest", args.payload_file)
    elif args.command == "post-servicerequest":
        _simulate_post("ServiceRequest", args.payload_file)


if __name__ == "__main__":
    main()
