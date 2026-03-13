#!/usr/bin/env python3
from __future__ import annotations

import argparse

from fhir_common import _get, _simulate_post


def main() -> None:
    parser = argparse.ArgumentParser(description='Simulate posting a vital-sign Observation payload from a JSON file.')
    parser.add_argument("--payload-file", required=True, help="Path to a JSON file containing one Observation payload.")
    args = parser.parse_args()
    _simulate_post("Observation", args.payload_file)


if __name__ == "__main__":
    main()
