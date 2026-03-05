"""Shared tool runtime context passed to tool handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolRuntime:
    fhir: Any | None = None
    resources: dict[str, Any] = field(default_factory=dict)

    def require_fhir(self) -> Any:
        if self.fhir is None:
            raise RuntimeError("FHIR client is not configured in tool_runtime.")
        return self.fhir
