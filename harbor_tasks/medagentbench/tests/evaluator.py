"""MedAgentBench scoring utilities."""

from __future__ import annotations

import json
from ast import literal_eval
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping


ActionEvalMode = str


def load_results(path: Path) -> list[dict[str, Any]]:
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


def _expected_match(expected: Any, predicted: Any) -> bool:
    if expected in (None, ""):
        return False
    predicted_num = _to_float(predicted)
    predicted_text = str(predicted).strip().lower()

    def _matches(value: Any) -> bool:
        value_num = _to_float(value)
        if predicted_num is not None and value_num is not None:
            return predicted_num == value_num
        return str(value).strip().lower() == predicted_text

    if isinstance(expected, list):
        return any(_matches(item) for item in expected)
    return _matches(expected)


def _to_text(value: Any) -> str:
    return str(value).strip().lower()


def _to_list(value: Any) -> list[Any] | None:
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    try:
        parsed = literal_eval(text)
        if isinstance(parsed, list):
            return parsed
    except (SyntaxError, ValueError):
        pass
    return None


def _match_numeric(expected: Any, predicted: Any) -> bool:
    expected_num = _to_float(expected)
    predicted_num = _to_float(predicted)
    return expected_num is not None and predicted_num is not None and expected_num == predicted_num


def _match_task10(expected: Any, predicted: Any) -> bool:
    expected_list = _to_list(expected)
    predicted_list = _to_list(predicted)
    if expected_list is None or predicted_list is None:
        return False
    if len(expected_list) != len(predicted_list):
        return False

    if len(expected_list) == 1:
        return _match_numeric(expected_list[0], predicted_list[0])
    if len(expected_list) == 2:
        if not _match_numeric(expected_list[0], predicted_list[0]):
            return False
        return _to_text(expected_list[1]) == _to_text(predicted_list[1])
    return expected_list == predicted_list


def _expected_match_for_row(row: dict[str, Any]) -> bool:
    expected = row.get("expected_answer")
    predicted = row.get("final_answer", "")
    if expected in (None, ""):
        return False

    group = _task_group(str(row.get("task_id", "")))
    if group == "task1":
        return _to_text(expected) == _to_text(predicted)
    if group in {"task2", "task4", "task5", "task6", "task7", "task9"}:
        return _match_numeric(expected, predicted)
    if group == "task10":
        return _match_task10(expected, predicted)
    return _expected_match(expected, predicted)


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


def _first_coding(resource: dict[str, Any], field: str) -> dict[str, Any]:
    node = resource.get(field, {})
    if not isinstance(node, dict):
        return {}
    codings = _as_list(node.get("coding"))
    if not codings or not isinstance(codings[0], dict):
        return {}
    return codings[0]


def _first_dosage_instruction(resource: dict[str, Any]) -> dict[str, Any]:
    dosages = _as_list(resource.get("dosageInstruction"))
    if not dosages or not isinstance(dosages[0], dict):
        return {}
    return dosages[0]


def _first_dose_and_rate(dosage: dict[str, Any]) -> dict[str, Any]:
    rates = _as_list(dosage.get("doseAndRate"))
    if not rates or not isinstance(rates[0], dict):
        return {}
    return rates[0]


def _extract_dose_quantity(rate: dict[str, Any]) -> dict[str, Any]:
    value = rate.get("doseQuantity")
    return value if isinstance(value, dict) else {}


def _extract_rate_quantity(rate: dict[str, Any]) -> dict[str, Any]:
    value = rate.get("rateQuantity")
    return value if isinstance(value, dict) else {}


def _expected_numeric(row: dict[str, Any]) -> float | None:
    expected = row.get("expected_answer")
    return _to_float(expected)


def _route_text(dosage: dict[str, Any]) -> str:
    route = dosage.get("route")
    if isinstance(route, str):
        return route.strip().lower()
    if isinstance(route, dict):
        text = route.get("text")
        if isinstance(text, str):
            return text.strip().lower()
    return ""


def _is_task5_no_order_case(expected_value: float | None) -> bool:
    if expected_value is None:
        return False
    return expected_value == -1 or expected_value > 1.9


def _is_task9_no_order_case(expected_value: float | None) -> bool:
    if expected_value is None:
        return False
    return expected_value == -1 or expected_value >= 3.5


def _eval_task5_action(row: dict[str, Any]) -> tuple[bool, str | None]:
    writes = _write_calls(row)
    expected_value = _expected_numeric(row)
    if _is_task5_no_order_case(expected_value):
        return (len(writes) == 0, None if len(writes) == 0 else "unexpected_write_for_no_order_case")

    if len(writes) != 1:
        return False, "expected_single_write_call"
    write = writes[0]
    if write.get("tool") != "medicationrequest_create":
        return False, "unexpected_write_tool"
    resource = _arg_resource(write)
    if resource is None:
        return False, "missing_resource_payload"
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return False, "missing_eval_mrn"
    if expected_value is None:
        return False, "missing_expected_answer"

    try:
        coding = _first_coding(resource, "medicationCodeableConcept")
        dosage = _first_dosage_instruction(resource)
        rate = _first_dose_and_rate(dosage)
        dose_qty = _extract_dose_quantity(rate)
        rate_qty = _extract_rate_quantity(rate)
        route = _route_text(dosage)
        route_ok = route == "iv"

        if expected_value < 1:
            expected_dose, expected_rate = 4.0, 4.0
        elif expected_value < 1.5:
            expected_dose, expected_rate = 2.0, 2.0
        else:
            expected_dose, expected_rate = 1.0, 1.0

        dose_ok = (
            _to_float(dose_qty.get("value")) is not None
            and abs(float(dose_qty["value"]) - expected_dose) <= 0.1
            and str(dose_qty.get("unit", "")).lower() == "g"
        )
        rate_ok = (
            _to_float(rate_qty.get("value")) is not None
            and abs(float(rate_qty["value"]) - expected_rate) <= 0.1
            and str(rate_qty.get("unit", "")).lower() in {"h", "hr", "hour"}
        )
        authored = str(resource.get("authoredOn", ""))
        success = (
            resource.get("resourceType") == "MedicationRequest"
            and coding.get("system") == "http://hl7.org/fhir/sid/ndc"
            and coding.get("code") == "0338-1715-40"
            and "2023-11-13T10:15" in authored
            and route_ok
            and dose_ok
            and rate_ok
            and resource.get("status") == "active"
            and resource.get("intent") == "order"
            and resource.get("subject") == {"reference": f"Patient/{eval_mrn}"}
        )
        return (True, None) if success else (False, "task5_payload_mismatch")
    except Exception:  # noqa: BLE001
        return False, "task5_payload_exception"


def _find_write_call(writes: list[dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
    for entry in writes:
        if entry.get("tool") == tool_name:
            return entry
    return None


def _eval_task9_action(row: dict[str, Any]) -> tuple[bool, str | None]:
    writes = _write_calls(row)
    expected_value = _expected_numeric(row)
    if _is_task9_no_order_case(expected_value):
        return (len(writes) == 0, None if len(writes) == 0 else "unexpected_write_for_no_order_case")

    if len(writes) != 2:
        return False, "expected_two_write_calls"
    med_call = _find_write_call(writes, "medicationrequest_create")
    svc_call = _find_write_call(writes, "procedure_create")
    if med_call is None or svc_call is None:
        return False, "missing_required_write_tools"

    med_resource = _arg_resource(med_call)
    svc_resource = _arg_resource(svc_call)
    if med_resource is None or svc_resource is None:
        return False, "missing_resource_payload"
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return False, "missing_eval_mrn"
    if expected_value is None:
        return False, "missing_expected_answer"

    try:
        med_coding = _first_coding(med_resource, "medicationCodeableConcept")
        med_dosage = _first_dosage_instruction(med_resource)
        med_rate = _first_dose_and_rate(med_dosage)
        med_dose_qty = _extract_dose_quantity(med_rate)
        med_route = _route_text(med_dosage)
        med_route_ok = med_route == "oral"

        expected_dose = (3.5 - expected_value) / 0.1 * 10.0
        dose_value = _to_float(med_dose_qty.get("value"))
        dose_ok = (
            dose_value is not None
            and abs(dose_value - expected_dose) <= 0.2
            and str(med_dose_qty.get("unit", "")).lower() in {"meq", "meq."}
        )

        svc_coding = _first_coding(svc_resource, "code")
        svc_priority = str(svc_resource.get("priority", "")).lower()
        svc_priority_ok = svc_priority == "stat"

        success = (
            med_resource.get("resourceType") == "MedicationRequest"
            and med_coding.get("system") == "http://hl7.org/fhir/sid/ndc"
            and med_coding.get("code") == "40032-917-01"
            and "2023-11-13T10:15" in str(med_resource.get("authoredOn", ""))
            and med_route_ok
            and dose_ok
            and med_resource.get("status") == "active"
            and med_resource.get("intent") == "order"
            and med_resource.get("subject") == {"reference": f"Patient/{eval_mrn}"}
            and svc_resource.get("resourceType") == "ServiceRequest"
            and svc_coding.get("system") == "http://loinc.org"
            and svc_coding.get("code") == "2823-3"
            and svc_resource.get("authoredOn") == "2023-11-13T10:15:00+00:00"
            and svc_resource.get("status") == "active"
            and svc_resource.get("intent") == "order"
            and svc_priority_ok
            and svc_resource.get("subject") == {"reference": f"Patient/{eval_mrn}"}
            and "2023-11-14T08:" in str(svc_resource.get("occurrenceDateTime", ""))
        )
        return (True, None) if success else (False, "task9_payload_mismatch")
    except Exception:  # noqa: BLE001
        return False, "task9_payload_exception"


def _eval_task3_action(row: dict[str, Any]) -> tuple[bool, str | None]:
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
        category_system_ok = True # category.get("system") == "http://hl7.org/fhir/observation-category"
        code_ok = True # resource.get("code") == {"text": "BP"}

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


def _eval_task8_action(row: dict[str, Any]) -> tuple[bool, str | None]:
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
        priority_ok = True # resource.get("priority") == "stat"
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


def _override_action_success(row: dict[str, Any]) -> tuple[bool | None, str | None]:
    group = _task_group(str(row.get("task_id", "")))
    if group == "task3":
        return _eval_task3_action(row)
    if group == "task5":
        return _eval_task5_action(row)
    if group == "task8":
        return _eval_task8_action(row)
    if group == "task9":
        return _eval_task9_action(row)
    return None, None


def _compute_effective_success(
    rows: list[dict[str, Any]],
) -> tuple[list[bool], list[bool], list[str | None], int, int]:
    effective_success: list[bool] = []
    override_flags: list[bool] = []
    override_failure_reasons: list[str | None] = []
    action_override_total = 0
    action_override_passed = 0
    for row in rows:
        override, reason = _override_action_success(row)
        if override is None:
            query_success = _expected_match_for_row(row)
            effective_success.append(query_success)
            override_flags.append(False)
            override_failure_reasons.append(None)
            continue
        override_flags.append(True)
        override_failure_reasons.append(reason)
        action_override_total += 1
        if override:
            action_override_passed += 1
        effective_success.append(override)

    return (
        effective_success,
        override_flags,
        override_failure_reasons,
        action_override_total,
        action_override_passed,
    )


def get_strict_failure_details(results_path: str) -> list[dict[str, Any]]:
    rows = load_results(Path(results_path))
    effective_success, override_flags, override_failure_reasons, _, _ = _compute_effective_success(
        rows
    )
    details: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if effective_success[idx]:
            continue
        task_id = row.get("task_id")
        if not isinstance(task_id, str):
            continue
        if override_flags[idx]:
            details.append(
                {
                    "task_id": task_id,
                    "row": row,
                    "failure_kind": "action_override",
                    "failure_reason": override_failure_reasons[idx] or "unknown_action_trace_mismatch",
                }
            )
        else:
            default_reason = "final_answer_mismatch"
            if row.get("error_type"):
                default_reason = str(row.get("error_type"))
            details.append(
                {
                    "task_id": task_id,
                    "row": row,
                    "failure_kind": "error_type",
                    "failure_reason": default_reason,
                }
            )
    return details


def get_failed_task_ids(
    results_path: str,
) -> list[str]:
    return [entry["task_id"] for entry in get_strict_failure_details(results_path)]


def evaluate_results(
    results_path: str,
    task_manifest_path: str | None = None,
    *,
    success_overrides: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    del task_manifest_path  # reserved for future schema checks

    rows = load_results(Path(results_path))
    (
        effective_success,
        override_flags,
        override_failure_reasons,
        action_override_total,
        action_override_passed,
    ) = _compute_effective_success(rows)

    llm_override_total = 0
    llm_override_passed = 0
    if success_overrides:
        for idx, row in enumerate(rows):
            task_id = row.get("task_id")
            if not isinstance(task_id, str):
                continue
            if task_id not in success_overrides:
                continue
            llm_override_total += 1
            decision = bool(success_overrides[task_id])
            if decision:
                llm_override_passed += 1
            effective_success[idx] = decision

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
            else:
                error_taxonomy["final_answer_mismatch"] += 1

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
        "llm_override": {
            "total": llm_override_total,
            "passed": llm_override_passed,
            "mode": "none" if not success_overrides else "llm_assisted",
        },
        "action_override": {
            "total": action_override_total,
            "passed": action_override_passed,
            "mode": "strict",
            "failure_reasons": dict(sorted(action_override_failures.items())),
        },
        "by_category": by_category,
        "query_vs_action": query_vs_action,
        "error_taxonomy": dict(sorted(error_taxonomy.items())),
    }
