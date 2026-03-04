"""Task-type evaluator adapter scaffold."""

from __future__ import annotations

from typing import Any


def evaluate_task(prediction: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": prediction.get("task_id") or reference.get("task_id"),
        "score": 0.0,
        "status": "adapter_not_implemented",
    }
