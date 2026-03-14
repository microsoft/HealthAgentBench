#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from fhir_common import _get, _simulate_post

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Retrieve Condition resources for a patient.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='Required flags: --patient',
    )
    parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")
    parser.add_argument("--category", help="Optional FHIR Condition category filter.")
    args = parser.parse_args()
    _get("Condition", {"patient": args.patient, "category": args.category})


if __name__ == "__main__":
    main()
