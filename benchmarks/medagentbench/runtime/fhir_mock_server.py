#!/usr/bin/env python3
"""Minimal FHIR-like HTTP server for local MedAgentBench smoke runs."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "0.0.0.0"
PORT = 8080

CAPABILITY_STATEMENT = {
    "resourceType": "CapabilityStatement",
    "status": "active",
    "kind": "instance",
    "fhirVersion": "4.0.1",
    "format": ["json"],
}


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/fhir+json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/metadata"):
            self._json(200, CAPABILITY_STATEMENT)
            return
        self._json(
            404,
            {
                "resourceType": "OperationOutcome",
                "issue": [{"severity": "error", "code": "not-found"}],
            },
        )

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> None:
    HTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
