#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from fhir_common import _get, _simulate_post

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Retrieve Patient resources using FHIR Patient search parameters.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=None,
    )
    parser.add_argument("--address", help="FHIR Patient search parameter: address")
    parser.add_argument("--address-city", help="FHIR Patient search parameter: address-city")
    parser.add_argument("--address-postalcode", help="FHIR Patient search parameter: address-postalcode")
    parser.add_argument("--address-state", help="FHIR Patient search parameter: address-state")
    parser.add_argument("--birthdate", help="FHIR Patient search parameter: birthdate")
    parser.add_argument("--family", help="FHIR Patient search parameter: family")
    parser.add_argument("--gender", help="FHIR Patient search parameter: gender")
    parser.add_argument("--given", help="FHIR Patient search parameter: given")
    parser.add_argument("--identifier", help="FHIR Patient search parameter: identifier")
    parser.add_argument("--legal-sex", help="FHIR Patient search parameter: legal-sex")
    parser.add_argument("--name", help="FHIR Patient search parameter: name")
    parser.add_argument("--telecom", help="FHIR Patient search parameter: telecom")
    args = parser.parse_args()
    _get("Patient", {"address": args.address, "address-city": args.address_city, "address-postalcode": args.address_postalcode, "address-state": args.address_state, "birthdate": args.birthdate, "family": args.family, "gender": args.gender, "given": args.given, "identifier": args.identifier, "legal-sex": args.legal_sex, "name": args.name, "telecom": args.telecom})


if __name__ == "__main__":
    main()
