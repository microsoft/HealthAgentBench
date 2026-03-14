#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from fhir_common import _get, _simulate_post

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Simulate posting a ServiceRequest payload from a JSON file.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='Original payload schema:\n\n{\n  "type": "object",\n  "properties": {\n    "resourceType": {\n      "type": "string",\n      "description": "Use \\"ServiceRequest\\" for service requests."\n    },\n    "code": {\n      "type": "object",\n      "description": "The standard terminology codes mapped to the procedure, which can include LOINC, SNOMED, CPT, CBV, THL, or Kuntalitto codes.",\n      "properties": {\n        "coding": {\n          "type": "array",\n          "items": {\n            "type": "object",\n            "properties": {\n              "system": {\n                "type": "string",\n                "description": "Coding system such as \\"http://loinc.org\\" "\n              },\n              "code": {\n                "type": "string",\n                "description": "The actual code"\n              },\n              "display": {\n                "type": "string",\n                "description": "Display name"\n              }\n            }\n          }\n        }\n      }\n    },\n    "authoredOn": {\n      "type": "string",\n      "description": "The order instant. This is the date and time of when an order is signed or signed and held."\n    },\n    "status": {\n      "type": "string",\n      "description": "The status of the service request. Use \\"active\\" "\n    },\n    "intent": {\n      "type": "string",\n      "description": "Use \\"order\\" "\n    },\n    "priority": {\n      "type": "string",\n      "description": "Use \\"stat\\" "\n    },\n    "subject": {\n      "type": "object",\n      "properties": {\n        "reference": {\n          "type": "string",\n          "description": "The patient FHIR ID for who the service request is for."\n        }\n      }\n    },\n    "note": {\n      "type": "object",\n      "properties": {\n        "text": {\n          "type": "string",\n          "description": "Free text comment here"\n        }\n      }\n    },\n    "occurrenceDateTime": {\n      "type": "string",\n      "description": "The date and time for the service request to be conducted, in ISO format."\n    }\n  },\n  "required": [\n    "resourceType",\n    "code",\n    "authoredOn",\n    "status",\n    "intent",\n    "priority",\n    "subject"\n  ]\n}',
    )
    parser.add_argument("--payload-file", required=True, help="Path to a JSON file containing one ServiceRequest payload.")
    args = parser.parse_args()
    _simulate_post("ServiceRequest", args.payload_file)


if __name__ == "__main__":
    main()
