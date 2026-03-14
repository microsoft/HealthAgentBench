#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from fhir_common import _get, _simulate_post

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Retrieve Procedure resources for a patient.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='Required flags: --date, --patient',
    )
    parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")
    parser.add_argument("--date", required=True, help="FHIR date filter expression.")
    parser.add_argument("--code", help="Optional Procedure code filter.")
    args = parser.parse_args()
    _get("Procedure", {"patient": args.patient, "date": args.date, "code": args.code})


if __name__ == "__main__":
    main()
