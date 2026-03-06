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


def _task_group(task_id: str) -> str:
    head = task_id.split("_", 1)[0]
    return head if head.startswith("task") else ""


def _write_calls(row: dict[str, Any]) -> list[dict[str, Any]]:
    trace = row.get("tool_trace", [])
    if not isinstance(trace, list):
        return []
    calls: list[dict[str, Any]] = []
    for entry in trace:
        if not isinstance(entry, dict):
            continue
        tool = entry.get("tool")
        if tool in {"vital_create", "procedure_create", "medicationrequest_create"}:
            calls.append(entry)
    return calls


def _arg_resource(entry: dict[str, Any]) -> dict[str, Any] | None:
    args = entry.get("args")
    if not isinstance(args, dict):
        return None
    resource = args.get("resource")
    return resource if isinstance(resource, dict) else None


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _eval_task3_action(row: dict[str, Any]) -> bool:
    writes = _write_calls(row)
    if len(writes) != 1:
        return False
    write = writes[0]
    if write.get("tool") != "vital_create":
        return False
    resource = _arg_resource(write)
    if resource is None:
        return False
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return False
    try:
        category_entries = _as_list(resource.get("category"))
        first_category = category_entries[0] if category_entries else {}
        coding_entries = _as_list(first_category.get("coding"))
        category = coding_entries[0] if coding_entries else {}
        return (
            resource["resourceType"] == "Observation"
            and category
            == {
                "system": "http://hl7.org/fhir/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs",
            }
            and resource["code"] == {"text": "BP"}
            and resource["effectiveDateTime"] == "2023-11-13T10:15:00+00:00"
            and resource["status"] == "final"
            and resource["valueString"] == "118/77 mmHg"
            and resource["subject"] == {"reference": f"Patient/{eval_mrn}"}
        )
    except Exception:  # noqa: BLE001
        return False


def _eval_task8_action(row: dict[str, Any]) -> bool:
    writes = _write_calls(row)
    if len(writes) != 1:
        return False
    write = writes[0]
    if write.get("tool") != "procedure_create":
        return False
    resource = _arg_resource(write)
    if resource is None:
        return False
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return False
    comment = (
        "Situation: acute left knee injury, Background: radiology report indicates ACL tear. "
        "Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to "
        "evaluate and provide management recommendations."
    )
    try:
        code = resource.get("code", {})
        coding_entries = _as_list(code.get("coding"))
        coding = coding_entries[0] if coding_entries else {}
        note_entries = _as_list(resource.get("note"))
        first_note = note_entries[0] if note_entries else {}
        note_text = first_note.get("text", "")
        return (
            resource["resourceType"] == "ServiceRequest"
            and coding["system"] == "http://snomed.info/sct"
            and coding["code"] == "306181000000106"
            and resource["authoredOn"] == "2023-11-13T10:15:00+00:00"
            and resource["status"] == "active"
            and resource["intent"] == "order"
            and resource["priority"] == "stat"
            and comment in note_text
            and resource["subject"] == {"reference": f"Patient/{eval_mrn}"}
        )
    except Exception:  # noqa: BLE001
        return False


def _override_action_success(row: dict[str, Any]) -> bool | None:
    group = _task_group(str(row.get("task_id", "")))
    if group == "task3":
        return _eval_task3_action(row)
    if group == "task8":
        return _eval_task8_action(row)
    return None


def evaluate_results(results_path: str, task_manifest_path: str | None = None) -> dict[str, Any]:
    del task_manifest_path  # reserved for future schema checks

    rows = _load_results(Path(results_path))
    effective_success: list[bool] = []
    override_flags: list[bool] = []
    action_override_total = 0
    action_override_passed = 0
    for row in rows:
        override = _override_action_success(row)
        if override is None:
            effective_success.append(bool(row.get("success")))
            override_flags.append(False)
            continue
        override_flags.append(True)
        action_override_total += 1
        if override:
            action_override_passed += 1
        effective_success.append(override)

    total = len(rows)
    passed = sum(1 for value in effective_success if value)
    pass_at_1 = (passed / total) if total else 0.0

    by_category_raw: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0})
    query_action_raw: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0})
    error_taxonomy: dict[str, int] = defaultdict(int)

    for idx, row in enumerate(rows):
        success = effective_success[idx]
        category = str(row.get("category", "unknown"))
        by_category_raw[category]["total"] += 1
        if success:
            by_category_raw[category]["passed"] += 1

        qtype = str(row.get("task_type", "unknown"))
        query_action_raw[qtype]["total"] += 1
        if success:
            query_action_raw[qtype]["passed"] += 1

        error_type = row.get("error_type")
        if not success:
            if override_flags[idx]:
                error_taxonomy["action_trace_validation_failed"] += 1
            elif error_type:
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
        "action_override": {
            "total": action_override_total,
            "passed": action_override_passed,
        },
        "by_category": by_category,
        "query_vs_action": query_vs_action,
        "error_taxonomy": dict(sorted(error_taxonomy.items())),
    }
