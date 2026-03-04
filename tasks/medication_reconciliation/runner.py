"""Task-type runner adapter scaffold."""

from __future__ import annotations

from typing import Any


def run_task(task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task.get("task_id"),
        "status": "adapter_not_implemented",
        "context": sorted(context.keys()),
    }
