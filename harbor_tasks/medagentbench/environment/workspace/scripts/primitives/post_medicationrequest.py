#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from fhir_common import _get, _simulate_post

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Simulate posting a MedicationRequest payload from a JSON file.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='Original payload schema:\n\n{\n  "type": "object",\n  "properties": {\n    "resourceType": {\n      "type": "string",\n      "description": "Use \\"MedicationRequest\\" for medication requests."\n    },\n    "medicationCodeableConcept": {\n      "type": "object",\n      "properties": {\n        "coding": {\n          "type": "array",\n          "items": {\n            "type": "object",\n            "properties": {\n              "system": {\n                "type": "string",\n                "description": "Coding system such as \\"http://hl7.org/fhir/sid/ndc\\" "\n              },\n              "code": {\n                "type": "string",\n                "description": "The actual code"\n              },\n              "display": {\n                "type": "string",\n                "description": "Display name"\n              }\n            }\n          }\n        },\n        "text": {\n          "type": "string",\n          "description": "The order display name of the medication, otherwise the record name."\n        }\n      }\n    },\n    "authoredOn": {\n      "type": "string",\n      "description": "The date the prescription was written."\n    },\n    "dosageInstruction": {\n      "type": "array",\n      "items": {\n        "type": "object",\n        "properties": {\n          "route": {\n            "type": "object",\n            "properties": {\n              "text": {\n                "type": "string",\n                "description": "The medication route."\n              }\n            }\n          },\n          "doseAndRate": {\n            "type": "array",\n            "items": {\n              "type": "object",\n              "properties": {\n                "doseQuantity": {\n                  "type": "object",\n                  "properties": {\n                    "value": {\n                      "type": "number"\n                    },\n                    "unit": {\n                      "type": "string",\n                      "description": "unit for the dose such as \\"g\\" "\n                    }\n                  }\n                },\n                "rateQuantity": {\n                  "type": "object",\n                  "properties": {\n                    "value": {\n                      "type": "number"\n                    },\n                    "unit": {\n                      "type": "string",\n                      "description": "unit for the rate such as \\"h\\" "\n                    }\n                  }\n                }\n              }\n            }\n          }\n        }\n      }\n    },\n    "status": {\n      "type": "string",\n      "description": "The status of the medication request. Use \\"active\\" "\n    },\n    "intent": {\n      "type": "string",\n      "description": "Use \\"order\\" "\n    },\n    "subject": {\n      "type": "object",\n      "properties": {\n        "reference": {\n          "type": "string",\n          "description": "The patient FHIR ID for who the medication request is for."\n        }\n      }\n    }\n  },\n  "required": [\n    "resourceType",\n    "medicationCodeableConcept",\n    "authoredOn",\n    "dosageInstruction",\n    "status",\n    "intent",\n    "subject"\n  ]\n}',
    )
    parser.add_argument("--payload-file", required=True, help="Path to a JSON file containing one MedicationRequest payload.")
    args = parser.parse_args()
    _simulate_post("MedicationRequest", args.payload_file)


if __name__ == "__main__":
    main()
