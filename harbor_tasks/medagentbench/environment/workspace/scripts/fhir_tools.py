#!/usr/bin/env python3
# Small helper CLI for reading the local FHIR server.

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Any


def _base_url() -> str:
    return os.environ.get("FHIR_BASE_URL", "http://fhir:8080/fhir").rstrip("/")


def _get_json(path: str) -> dict[str, Any]:
    url = f"{_base_url()}/{path.lstrip('/')}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _patient_search(name: str | None, birthdate: str | None, mrn: str | None) -> None:
    if mrn:
        query = f"Patient?identifier={urllib.parse.quote(mrn)}&_format=json"
    else:
        params = []
        if name:
            params.append(f"name={urllib.parse.quote(name)}")
        if birthdate:
            params.append(f"birthdate={urllib.parse.quote(birthdate)}")
        params.append("_format=json")
        query = "Patient?" + "&".join(params)
    _print(_get_json(query))


def _observation_search(patient: str, code: str) -> None:
    query = (
        f"Observation?patient={urllib.parse.quote(patient)}"
        f"&code={urllib.parse.quote(code)}&_count=5000&_format=json"
    )
    _print(_get_json(query))


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _observations(patient: str, code: str) -> list[dict[str, Any]]:
    bundle = _get_json(
        f"Observation?patient={urllib.parse.quote(patient)}&code={urllib.parse.quote(code)}&_count=5000&_format=json"
    )
    return [entry.get("resource", {}) for entry in bundle.get("entry", []) if isinstance(entry, dict)]


def _quantity_value(resource: dict[str, Any]) -> float | None:
    value = resource.get("valueQuantity", {}).get("value")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _latest_observation(patient: str, code: str, within_hours: int | None) -> None:
    cutoff = None
    if within_hours is not None:
        cutoff = datetime.fromisoformat("2023-11-13T10:15:00+00:00") - timedelta(hours=within_hours)
    best = None
    best_dt = None
    for resource in _observations(patient, code):
        effective_dt = _parse_dt(resource.get("effectiveDateTime"))
        if effective_dt is None:
            continue
        if cutoff is not None and effective_dt < cutoff:
            continue
        if best_dt is None or effective_dt > best_dt:
            best_dt = effective_dt
            best = resource
    _print(best or {})


def _average_observation(patient: str, code: str, within_hours: int) -> None:
    cutoff = datetime.fromisoformat("2023-11-13T10:15:00+00:00") - timedelta(hours=within_hours)
    values: list[float] = []
    for resource in _observations(patient, code):
        effective_dt = _parse_dt(resource.get("effectiveDateTime"))
        value = _quantity_value(resource)
        if effective_dt is None or value is None:
            continue
        if effective_dt >= cutoff:
            values.append(value)
    payload = {
        "count": len(values),
        "average": -1 if not values else sum(values) / len(values),
        "values": values,
    }
    _print(payload)


def _patient_age(mrn: str, reference_time: str) -> None:
    bundle = _get_json(f"Patient?identifier={urllib.parse.quote(mrn)}&_format=json")
    entries = bundle.get("entry", [])
    if not entries:
        _print({"mrn": mrn, "age": -1, "error": "Patient not found"})
        return
    resource = entries[0].get("resource", {})
    birthdate = resource.get("birthDate")
    if not birthdate:
        _print({"mrn": mrn, "age": -1, "error": "birthDate missing"})
        return
    dob = datetime.strptime(birthdate, "%Y-%m-%d")
    now = datetime.fromisoformat(reference_time)
    age = now.year - dob.year
    if (now.month, now.day) < (dob.month, dob.day):
        age -= 1
    _print({"mrn": mrn, "birthDate": birthdate, "age": age})


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    patient_parser = subparsers.add_parser("patient-search")
    patient_parser.add_argument("--name")
    patient_parser.add_argument("--birthdate")
    patient_parser.add_argument("--mrn")

    observation_parser = subparsers.add_parser("observation-search")
    observation_parser.add_argument("--patient", required=True)
    observation_parser.add_argument("--code", required=True)

    latest_parser = subparsers.add_parser("latest-observation")
    latest_parser.add_argument("--patient", required=True)
    latest_parser.add_argument("--code", required=True)
    latest_parser.add_argument("--within-hours", type=int)

    average_parser = subparsers.add_parser("average-observation")
    average_parser.add_argument("--patient", required=True)
    average_parser.add_argument("--code", required=True)
    average_parser.add_argument("--within-hours", type=int, required=True)

    age_parser = subparsers.add_parser("patient-age")
    age_parser.add_argument("--mrn", required=True)
    age_parser.add_argument("--reference-time", default="2023-11-13T10:15:00+00:00")

    args = parser.parse_args()
    if args.command == "patient-search":
        _patient_search(args.name, args.birthdate, args.mrn)
    elif args.command == "observation-search":
        _observation_search(args.patient, args.code)
    elif args.command == "latest-observation":
        _latest_observation(args.patient, args.code, args.within_hours)
    elif args.command == "average-observation":
        _average_observation(args.patient, args.code, args.within_hours)
    elif args.command == "patient-age":
        _patient_age(args.mrn, args.reference_time)


if __name__ == "__main__":
    main()
