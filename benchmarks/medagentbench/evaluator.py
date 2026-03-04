"""MedAgentBench scoring utilities."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_results(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def evaluate_results(results_path: str, task_manifest_path: str | None = None) -> dict[str, Any]:
    del task_manifest_path  # reserved for future schema checks

    rows = _load_results(Path(results_path))
    total = len(rows)
    passed = sum(1 for row in rows if bool(row.get("success")))
    pass_at_1 = (passed / total) if total else 0.0

    by_category_raw: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0})
    query_action_raw: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0})
    error_taxonomy: dict[str, int] = defaultdict(int)

    for row in rows:
        category = str(row.get("category", "unknown"))
        by_category_raw[category]["total"] += 1
        if bool(row.get("success")):
            by_category_raw[category]["passed"] += 1

        qtype = str(row.get("task_type", "unknown"))
        query_action_raw[qtype]["total"] += 1
        if bool(row.get("success")):
            query_action_raw[qtype]["passed"] += 1

        error_type = row.get("error_type")
        if error_type:
            error_taxonomy[str(error_type)] += 1

    by_category = {
        key: {
            "total": value["total"],
            "passed": value["passed"],
            "pass_at_1": (value["passed"] / value["total"]) if value["total"] else 0.0,
        }
        for key, value in sorted(by_category_raw.items())
    }

    query_vs_action = {
        key: {
            "total": value["total"],
            "passed": value["passed"],
            "pass_at_1": (value["passed"] / value["total"]) if value["total"] else 0.0,
        }
        for key, value in sorted(query_action_raw.items())
    }

    return {
        "pass_at_1": pass_at_1,
        "total_tasks": total,
        "passed_tasks": passed,
        "by_category": by_category,
        "query_vs_action": query_vs_action,
        "error_taxonomy": dict(sorted(error_taxonomy.items())),
    }
