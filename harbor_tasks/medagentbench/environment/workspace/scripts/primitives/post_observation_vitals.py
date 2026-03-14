#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from fhir_common import _get, _simulate_post

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Simulate posting a vital-sign Observation payload from a JSON file.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='Original payload schema:\n\n{\n  "type": "object",\n  "properties": {\n    "resourceType": {\n      "type": "string",\n      "description": "Use \\"Observation\\" for vitals observations."\n    },\n    "category": {\n      "type": "array",\n      "items": {\n        "type": "object",\n        "properties": {\n          "coding": {\n            "type": "array",\n            "items": {\n              "type": "object",\n              "properties": {\n                "system": {\n                  "type": "string",\n                  "description": "Use \\"http://hl7.org/fhir/observation-category\\" "\n                },\n                "code": {\n                  "type": "string",\n                  "description": "Use \\"vital-signs\\" "\n                },\n                "display": {\n                  "type": "string",\n                  "description": "Use \\"Vital Signs\\" "\n                }\n              }\n            }\n          }\n        }\n      }\n    },\n    "code": {\n      "type": "object",\n      "properties": {\n        "text": {\n          "type": "string",\n          "description": "The flowsheet ID, encoded flowsheet ID, or LOINC codes to flowsheet mapping. What is being measured."\n        }\n      }\n    },\n    "effectiveDateTime": {\n      "type": "string",\n      "description": "The date and time the observation was taken, in ISO format."\n    },\n    "status": {\n      "type": "string",\n      "description": "The status of the observation. Only a value of \\"final\\" is supported. We do not support filing data that isn\'t finalized."\n    },\n    "valueString": {\n      "type": "string",\n      "description": "Measurement value"\n    },\n    "subject": {\n      "type": "object",\n      "properties": {\n        "reference": {\n          "type": "string",\n          "description": "The patient FHIR ID for whom the observation is about."\n        }\n      }\n    }\n  },\n  "required": [\n    "resourceType",\n    "category",\n    "code",\n    "effectiveDateTime",\n    "status",\n    "valueString",\n    "subject"\n  ]\n}',
    )
    parser.add_argument("--payload-file", required=True, help="Path to a JSON file containing one Observation payload.")
    args = parser.parse_args()
    _simulate_post("Observation", args.payload_file)


if __name__ == "__main__":
    main()
