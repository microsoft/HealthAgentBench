"""Task registry and discovery entrypoint.

This module is intentionally minimal during scaffold phase.
Task-type packages should be discoverable under ``tasks/<task_type>/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TaskPackage:
    name: str
    path: Path


def discover_task_packages(root: Path | None = None) -> list[TaskPackage]:
    """Return task package directories containing a ``task.yaml`` file."""
    base = root or Path(__file__).resolve().parent
    packages: list[TaskPackage] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name == "selectors":
            continue
        if (child / "task.yaml").exists():
            packages.append(TaskPackage(name=child.name, path=child))
    return packages
