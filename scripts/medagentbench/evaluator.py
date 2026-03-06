"""MedAgentBench scoring utilities."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal


ActionEvalMode = Literal["strict", "balanced"]

_OBSERVATION_CATEGORY_SYSTEM_ALIASES = {
    "http://hl7.org/fhir/observation-category",
    "http://terminology.hl7.org/CodeSystem/observation-category",
}


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


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _contains_unavailable_semantics(text: str) -> bool:
    lowered = text.lower()
    phrases = (
        "not available",
        "not found",
        "no measurement",
        "no result",
        "no lab",
        "no record",
        "no serum",
    )
    if any(phrase in lowered for phrase in phrases):
        return True
    return bool(
        re.search(r"\bno\b.{0,40}\b(available|result|recorded|measurement|found)\b", lowered)
    )


def _balanced_query_success(row: dict[str, Any]) -> bool | None:
    if str(row.get("task_type")) != "query":
        return None
    expected = row.get("expected_answer")
    final_answer = row.get("final_answer")
    if final_answer is None:
        return None
    final_text = str(final_answer)

    expected_num = _to_float(expected)
    if expected_num is None:
        expected_str = str(expected).strip()
        if not expected_str:
            return None
        return expected_str in final_text

    direct = _to_float(final_answer)
    if direct is not None and abs(direct - expected_num) <= 1e-6:
        return True

    if expected_num == -1 and _contains_unavailable_semantics(final_text):
        return True

    numeric_tokens = re.findall(r"[-+]?\d*\.?\d+", final_text)
    for token in numeric_tokens:
        try:
            value = float(token)
        except ValueError:
            continue
        if abs(value - expected_num) <= 1e-6:
            return True
    return False


def _is_balanced_bp_code(resource: dict[str, Any]) -> bool:
    code = resource.get("code")
    if not isinstance(code, dict):
        return False
    text = str(code.get("text", "")).strip().lower()
    if text == "bp":
        return True
    return "blood pressure" in text


def _eval_task3_action(
    row: dict[str, Any], *, mode: ActionEvalMode
) -> tuple[bool, str | None]:
    writes = _write_calls(row)
    if len(writes) != 1:
        return False, "expected_single_write_call"
    write = writes[0]
    if write.get("tool") != "vital_create":
        return False, "unexpected_write_tool"
    resource = _arg_resource(write)
    if resource is None:
        return False, "missing_resource_payload"
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return False, "missing_eval_mrn"
    try:
        category_entries = _as_list(resource.get("category"))
        first_category = category_entries[0] if category_entries else {}
        coding_entries = _as_list(first_category.get("coding"))
        category = coding_entries[0] if coding_entries else {}
        category_system = category.get("system")
        category_system_ok = category_system == "http://hl7.org/fhir/observation-category"
        if mode == "balanced":
            category_system_ok = category_system in _OBSERVATION_CATEGORY_SYSTEM_ALIASES
        code_ok = resource.get("code") == {"text": "BP"}
        if mode == "balanced":
            code_ok = _is_balanced_bp_code(resource)

        success = (
            resource["resourceType"] == "Observation"
            and category_system_ok
            and category.get("code") == "vital-signs"
            and category.get("display") == "Vital Signs"
            and code_ok
            and resource["effectiveDateTime"] == "2023-11-13T10:15:00+00:00"
            and resource["status"] == "final"
            and resource["valueString"] == "118/77 mmHg"
            and resource["subject"] == {"reference": f"Patient/{eval_mrn}"}
        )
        return (True, None) if success else (False, "task3_payload_mismatch")
    except Exception:  # noqa: BLE001
        return False, "task3_payload_exception"


def _eval_task8_action(
    row: dict[str, Any], *, mode: ActionEvalMode
) -> tuple[bool, str | None]:
    writes = _write_calls(row)
    if len(writes) != 1:
        return False, "expected_single_write_call"
    write = writes[0]
    if write.get("tool") != "procedure_create":
        return False, "unexpected_write_tool"
    resource = _arg_resource(write)
    if resource is None:
        return False, "missing_resource_payload"
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return False, "missing_eval_mrn"
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
        priority = resource.get("priority")
        priority_ok = priority == "stat"
        if mode == "balanced":
            priority_ok = priority in {"stat", "urgent", "routine"}
        success = (
            resource["resourceType"] == "ServiceRequest"
            and coding["system"] == "http://snomed.info/sct"
            and coding["code"] == "306181000000106"
            and resource["authoredOn"] == "2023-11-13T10:15:00+00:00"
            and resource["status"] == "active"
            and resource["intent"] == "order"
            and priority_ok
            and comment in note_text
            and resource["subject"] == {"reference": f"Patient/{eval_mrn}"}
        )
        return (True, None) if success else (False, "task8_payload_mismatch")
    except Exception:  # noqa: BLE001
        return False, "task8_payload_exception"


def _override_action_success(
    row: dict[str, Any], *, mode: ActionEvalMode
) -> tuple[bool | None, str | None]:
    group = _task_group(str(row.get("task_id", "")))
    if group == "task3":
        return _eval_task3_action(row, mode=mode)
    if group == "task8":
        return _eval_task8_action(row, mode=mode)
    return None, None


def evaluate_results(
    results_path: str,
    task_manifest_path: str | None = None,
    *,
    action_eval_mode: ActionEvalMode = "strict",
) -> dict[str, Any]:
    del task_manifest_path  # reserved for future schema checks

    rows = _load_results(Path(results_path))
    effective_success: list[bool] = []
    override_flags: list[bool] = []
    override_failure_reasons: list[str | None] = []
    action_override_total = 0
    action_override_passed = 0
    for row in rows:
        override, reason = _override_action_success(row, mode=action_eval_mode)
        if override is None:
            balanced_query = (
                _balanced_query_success(row) if action_eval_mode == "balanced" else None
            )
            if balanced_query is None:
                effective_success.append(bool(row.get("success")))
            else:
                effective_success.append(bool(balanced_query))
            override_flags.append(False)
            override_failure_reasons.append(None)
            continue
        override_flags.append(True)
        override_failure_reasons.append(reason)
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
    action_override_failures: dict[str, int] = defaultdict(int)

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
                reason = override_failure_reasons[idx] or "unknown_action_trace_mismatch"
                action_override_failures[reason] += 1
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
            "mode": action_eval_mode,
            "failure_reasons": dict(sorted(action_override_failures.items())),
        },
        "by_category": by_category,
        "query_vs_action": query_vs_action,
        "error_taxonomy": dict(sorted(error_taxonomy.items())),
    }
