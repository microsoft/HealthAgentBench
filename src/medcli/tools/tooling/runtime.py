"""Shared tool runtime context passed to tool handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolRuntime:
    """Container for runtime-bound clients/resources used by tool handlers."""

    fhir: Any | None = None
    resources: dict[str, Any] = field(default_factory=dict)

    def require_fhir(self) -> Any:
        """Return configured FHIR client or raise with actionable error."""
        if self.fhir is None:
            raise RuntimeError("FHIR client is not configured in tool_runtime.")
        return self.fhir
