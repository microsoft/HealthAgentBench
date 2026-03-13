#!/usr/bin/env python3
from __future__ import annotations

import argparse

from fhir_common import _get, _simulate_post


def main() -> None:
    parser = argparse.ArgumentParser(description='Retrieve MedicationRequest resources for a patient.')
    parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")
    parser.add_argument("--category", help="Optional MedicationRequest category filter.")
    parser.add_argument("--date", help="Optional FHIR date filter expression.")
    args = parser.parse_args()
    _get("MedicationRequest", {"patient": args.patient, "category": args.category, "date": args.date})


if __name__ == "__main__":
    main()
