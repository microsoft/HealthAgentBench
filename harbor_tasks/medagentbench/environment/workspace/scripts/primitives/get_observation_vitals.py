#!/usr/bin/env python3
from __future__ import annotations

import argparse

from fhir_common import _get, _simulate_post


def main() -> None:
    parser = argparse.ArgumentParser(description='Retrieve vital-sign Observation resources for a patient and category.')
    parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")
    parser.add_argument("--category", required=True, help="Observation category filter, such as vital-signs.")
    parser.add_argument("--date", help="Optional FHIR date filter expression.")
    args = parser.parse_args()
    _get("Observation", {"patient": args.patient, "category": args.category, "date": args.date})


if __name__ == "__main__":
    main()
