"""Harbor-specific MedAgentBench evaluator for raw-task submissions."""

from __future__ import annotations

import json
from ast import literal_eval
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


REFERENCE_TIME = datetime.fromisoformat("2023-11-13T10:15:00+00:00")


def load_submission(path: Path) -> list[dict[str, Any]]:
    """Load Harbor submission rows from either a plain list or wrapped object."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        rows = payload["results"]
    else:
        raise ValueError("Submission JSON must be a list or an object with a 'results' list.")
    return [row for row in rows if isinstance(row, dict)]


def merge_submission_with_answer_key(
    submission_rows: list[dict[str, Any]], answer_key_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Join public submission rows with hidden verifier rows by task id."""
    answers_by_id = {
        str(row.get("task_id", row.get("id", ""))): row
        for row in answer_key_rows
        if isinstance(row, dict)
    }
    merged: list[dict[str, Any]] = []
    for row in submission_rows:
        if not isinstance(row, dict):
            continue
        task_id = str(row.get("task_id", row.get("id", "")))
        merged_row = dict(answers_by_id.get(task_id, {}))
        merged_row.update(row)
        if "id" not in merged_row and task_id:
            merged_row["id"] = task_id
        if "task_id" not in merged_row and task_id:
            merged_row["task_id"] = task_id
        merged.append(merged_row)
    return merged


def _task_group(task_id: str) -> str:
    head = task_id.split("_", 1)[0]
    return head if head.startswith("task") else ""


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


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


def _payload_list(row: dict[str, Any]) -> list[dict[str, Any]]:
    payload = row.get("payload")
    if payload is None:
        return []
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]
    return []


def _payload_object(row: dict[str, Any]) -> dict[str, Any] | None:
    items = _payload_list(row)
    if len(items) != 1:
        return None
    return items[0]


def _expected(row: dict[str, Any]) -> Any:
    value = row.get("sol", "")
    if isinstance(value, list) and len(value) == 1:
        single = value[0]
        if _task_group(str(row.get("id", ""))) == "task10" and single == -1:
            return [-1]
        return single
    return value


def _match_numeric(expected: Any, predicted: Any, *, tolerance: float = 0.0) -> bool:
    expected_num = _to_float(expected)
    predicted_num = _to_float(predicted)
    return (
        expected_num is not None
        and predicted_num is not None
        and abs(expected_num - predicted_num) <= tolerance
    )


def _match_task10(expected: Any, predicted: Any) -> bool:
    expected_list = expected if isinstance(expected, list) else _to_list(expected)
    predicted_list = predicted if isinstance(predicted, list) else _to_list(predicted)
    if expected_list is None or predicted_list is None or len(expected_list) != len(predicted_list):
        return False
    if len(expected_list) == 1:
        return _match_numeric(expected_list[0], predicted_list[0])
    if len(expected_list) == 2:
        return _match_numeric(expected_list[0], predicted_list[0]) and _to_text(expected_list[1]) == _to_text(
            predicted_list[1]
        )
    return expected_list == predicted_list


def _final_answer_success(row: dict[str, Any]) -> bool:
    expected = _expected(row)
    predicted = row.get("final_answer", "")
    group = _task_group(str(row.get("id", "")))
    if expected in (None, "") and group not in {"task3", "task8"}:
        return False
    if group in {"task3", "task8"}:
        return True
    if group == "task1":
        return _to_text(expected) == _to_text(predicted)
    if group == "task6":
        return _match_numeric(expected, predicted, tolerance=0.1)
    if group in {"task2", "task4", "task5", "task7", "task9"}:
        return _match_numeric(expected, predicted)
    if group == "task10":
        return _match_task10(expected, predicted)
    return _to_text(expected) == _to_text(predicted)


def _service_request_hba1c(payload: dict[str, Any], eval_mrn: str) -> bool:
    coding = ((payload.get("code") or {}).get("coding") or [{}])[0]
    return (
        payload.get("resourceType") == "ServiceRequest"
        and coding.get("system") == "http://loinc.org"
        and coding.get("code") == "4548-4"
        and payload.get("authoredOn") == "2023-11-13T10:15:00+00:00"
        and payload.get("status") == "active"
        and payload.get("intent") == "order"
        and payload.get("priority") == "stat"
        and payload.get("subject") == {"reference": f"Patient/{eval_mrn}"}
    )


def _eval_task3_payload(row: dict[str, Any]) -> bool:
    payload = _payload_object(row)
    eval_mrn = str(row.get("eval_MRN", ""))
    if payload is None or not eval_mrn:
        return False
    coding = ((payload.get("category") or [{}])[0].get("coding") or [{}])[0]
    return (
        payload.get("resourceType") == "Observation"
        and coding == {
            "system": "http://hl7.org/fhir/observation-category",
            "code": "vital-signs",
            "display": "Vital Signs",
        }
        and payload.get("code") == {"text": "BP"}
        and payload.get("effectiveDateTime") == "2023-11-13T10:15:00+00:00"
        and payload.get("status") == "final"
        and payload.get("valueString") == "118/77 mmHg"
        and payload.get("subject") == {"reference": f"Patient/{eval_mrn}"}
    )


def _eval_task5_payload(row: dict[str, Any]) -> bool:
    expected = _to_float(_expected(row))
    if expected is None:
        return False
    payloads = _payload_list(row)
    if expected == -1 or expected > 1.9:
        return len(payloads) == 0
    if len(payloads) != 1:
        return False
    payload = payloads[0]
    eval_mrn = str(row.get("eval_MRN", ""))
    coding = ((payload.get("medicationCodeableConcept") or {}).get("coding") or [{}])[0]
    dosage = ((payload.get("dosageInstruction") or [{}])[0])
    dose_and_rate = ((dosage.get("doseAndRate") or [{}])[0])
    if expected < 1:
        dose, rate = 4.0, 4.0
    elif expected < 1.5:
        dose, rate = 2.0, 2.0
    else:
        dose, rate = 1.0, 1.0
    return (
        payload.get("resourceType") == "MedicationRequest"
        and coding.get("system") == "http://hl7.org/fhir/sid/ndc"
        and coding.get("code") == "0338-1715-40"
        and "2023-11-13T10:15" in str(payload.get("authoredOn", ""))
        and dosage.get("route") == "IV"
        and dose_and_rate.get("doseQuantity") == {"value": dose, "unit": "g"}
        and dose_and_rate.get("rateQuantity") == {"value": rate, "unit": "h"}
        and payload.get("status") == "active"
        and payload.get("intent") == "order"
        and payload.get("subject") == {"reference": f"Patient/{eval_mrn}"}
    )


def _eval_task8_payload(row: dict[str, Any]) -> bool:
    payload = _payload_object(row)
    eval_mrn = str(row.get("eval_MRN", ""))
    if payload is None or not eval_mrn:
        return False
    coding = ((payload.get("code") or {}).get("coding") or [{}])[0]
    note = payload.get("note") or {}
    if isinstance(note, list):
        note = note[0] if note else {}
    comment = (
        "Situation: acute left knee injury, Background: radiology report indicates ACL tear. "
        "Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to "
        "evaluate and provide management recommendations."
    )
    return (
        payload.get("resourceType") == "ServiceRequest"
        and coding.get("system") == "http://snomed.info/sct"
        and coding.get("code") == "306181000000106"
        and payload.get("authoredOn") == "2023-11-13T10:15:00+00:00"
        and payload.get("status") == "active"
        and payload.get("intent") == "order"
        and payload.get("priority") == "stat"
        and comment in str(note.get("text", ""))
        and payload.get("subject") == {"reference": f"Patient/{eval_mrn}"}
    )


def _eval_task9_payload(row: dict[str, Any]) -> bool:
    expected = _to_float(_expected(row))
    if expected is None:
        return False
    payloads = _payload_list(row)
    if expected == -1 or expected >= 3.5:
        return len(payloads) == 0
    if len(payloads) != 2:
        return False
    med_payload, svc_payload = payloads
    eval_mrn = str(row.get("eval_MRN", ""))
    med_coding = ((med_payload.get("medicationCodeableConcept") or {}).get("coding") or [{}])[0]
    med_dosage = ((med_payload.get("dosageInstruction") or [{}])[0])
    med_rate = ((med_dosage.get("doseAndRate") or [{}])[0])
    expected_dose = (3.5 - expected) / 0.1 * 10.0
    svc_coding = ((svc_payload.get("code") or {}).get("coding") or [{}])[0]
    return (
        med_payload.get("resourceType") == "MedicationRequest"
        and med_coding.get("system") == "http://hl7.org/fhir/sid/ndc"
        and med_coding.get("code") == "40032-917-01"
        and "2023-11-13T10:15" in str(med_payload.get("authoredOn", ""))
        and str(med_dosage.get("route", "")).lower().strip() == "oral"
        and abs(float(med_rate.get("doseQuantity", {}).get("value", -999)) - expected_dose) <= 0.1
        and med_rate.get("doseQuantity", {}).get("unit") == "mEq"
        and med_payload.get("status") == "active"
        and med_payload.get("intent") == "order"
        and med_payload.get("subject") == {"reference": f"Patient/{eval_mrn}"}
        and svc_payload.get("resourceType") == "ServiceRequest"
        and svc_coding.get("system") == "http://loinc.org"
        and svc_coding.get("code") == "2823-3"
        and svc_payload.get("authoredOn") == "2023-11-13T10:15:00+00:00"
        and svc_payload.get("status") == "active"
        and svc_payload.get("intent") == "order"
        and svc_payload.get("priority") == "stat"
        and svc_payload.get("subject") == {"reference": f"Patient/{eval_mrn}"}
        and "2023-11-14T08:" in str(svc_payload.get("occurrenceDateTime", ""))
    )


def _eval_task10_payload(row: dict[str, Any]) -> bool:
    payloads = _payload_list(row)
    eval_mrn = str(row.get("eval_MRN", ""))
    expected = _expected(row)
    order_required = False
    if expected == [-1]:
        order_required = True
    elif isinstance(expected, list) and len(expected) == 2:
        try:
            observed_at = datetime.fromisoformat(str(expected[1]))
        except ValueError:
            observed_at = None
        order_required = observed_at is None or observed_at < (REFERENCE_TIME - timedelta(days=365))
    if not order_required:
        return len(payloads) == 0
    if len(payloads) != 1 or not eval_mrn:
        return False
    return _service_request_hba1c(payloads[0], eval_mrn)


def _payload_success(row: dict[str, Any]) -> bool:
    group = _task_group(str(row.get("id", "")))
    if group == "task3":
        return _eval_task3_payload(row)
    if group == "task5":
        return _eval_task5_payload(row)
    if group == "task8":
        return _eval_task8_payload(row)
    if group == "task9":
        return _eval_task9_payload(row)
    if group == "task10":
        return _eval_task10_payload(row)
    return len(_payload_list(row)) == 0


def evaluate_submission_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate Harbor submission rows and return summary metrics."""
    total = len(rows)
    passed = 0
    failures: dict[str, int] = {}
    row_summaries: list[dict[str, Any]] = []
    for row in rows:
        task_id = str(row.get("id", row.get("task_id", "")))
        final_ok = _final_answer_success(row)
        payload_ok = _payload_success(row)
        success = final_ok and payload_ok
        if success:
            passed += 1
            failure_reason = None
        elif not final_ok and not payload_ok:
            failure_reason = "final_answer_and_payload_mismatch"
        elif not final_ok:
            failure_reason = "final_answer_mismatch"
        else:
            failure_reason = "payload_mismatch"
        if failure_reason:
            failures[failure_reason] = failures.get(failure_reason, 0) + 1
        row_summaries.append(
            {
                "task_id": task_id,
                "success": success,
                "final_answer": row.get("final_answer"),
                "payload": row.get("payload"),
                "failure_reason": failure_reason,
            }
        )
    return {
        "total_tasks": total,
        "passed_tasks": passed,
        "pass_at_1": 0.0 if total == 0 else passed / total,
        "error_taxonomy": failures,
        "results": row_summaries,
    }
