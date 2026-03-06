"""Batch LLM adjudication for strict-mode MedAgentBench failures."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Literal

from ehr_co_scientist.backends.azure_openai import run_direct_chat_completion


JudgeCaseType = Literal["query_compare", "action_payload_compare"]


@dataclass(frozen=True)
class LLMJudgeConfig:
    model: str = "o4-mini"
    backend: str = "azure_openai"
    api_version: str = "2025-03-01-preview"
    endpoint_name: str | None = None
    temperature: float = 0.0
    max_cases: int | None = None
    batch_size: int = 20
    max_batches: int | None = None


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


def _extract_json_payload(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _normalize_judgments(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("judgments"), list):
        rows = payload["judgments"]
    elif isinstance(payload, list):
        rows = payload
    else:
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        task_id = row.get("task_id")
        verdict = str(row.get("verdict", "")).strip().lower()
        if not isinstance(task_id, str) or verdict not in {"pass", "fail"}:
            continue
        normalized.append(
            {
                "task_id": task_id,
                "verdict": verdict,
                "confidence": str(row.get("confidence", "unknown")),
                "reason": str(row.get("reason", "")),
            }
        )
    return normalized


def _extract_tool_resource(row: dict[str, Any], tool_name: str) -> dict[str, Any] | None:
    trace = row.get("tool_trace")
    if not isinstance(trace, list):
        return None
    for entry in trace:
        if not isinstance(entry, dict):
            continue
        if entry.get("tool") != tool_name:
            continue
        args = entry.get("args")
        if not isinstance(args, dict):
            return None
        resource = args.get("resource")
        return resource if isinstance(resource, dict) else None
    return None


def _build_expected_task3_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return None
    return {
        "vital_create": {
            "resourceType": "Observation",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs",
                        }
                    ]
                }
            ],
            "code": {"text": "BP"},
            "effectiveDateTime": "2023-11-13T10:15:00+00:00",
            "status": "final",
            "valueString": "118/77 mmHg",
            "subject": {"reference": f"Patient/{eval_mrn}"},
        }
    }


def _build_expected_task8_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    eval_mrn = row.get("eval_mrn")
    if not isinstance(eval_mrn, str) or not eval_mrn:
        return None
    comment = (
        "Situation: acute left knee injury, Background: radiology report indicates ACL tear. "
        "Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to "
        "evaluate and provide management recommendations."
    )
    return {
        "procedure_create": {
            "resourceType": "ServiceRequest",
            "code": {
                "coding": [{"system": "http://snomed.info/sct", "code": "306181000000106"}]
            },
            "authoredOn": "2023-11-13T10:15:00+00:00",
            "status": "active",
            "intent": "order",
            "priority": "stat",
            "note": {"text": comment},
            "subject": {"reference": f"Patient/{eval_mrn}"},
        }
    }


def _build_expected_task5_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    eval_mrn = row.get("eval_mrn")
    expected = _to_float(row.get("expected_answer"))
    if not isinstance(eval_mrn, str) or not eval_mrn or expected is None:
        return None
    if expected < 1:
        dose, rate = 4.0, 4.0
    elif expected < 1.5:
        dose, rate = 2.0, 2.0
    else:
        dose, rate = 1.0, 1.0
    return {
        "medicationrequest_create": {
            "resourceType": "MedicationRequest",
            "medicationCodeableConcept": {
                "coding": [{"system": "http://hl7.org/fhir/sid/ndc", "code": "0338-1715-40"}]
            },
            "authoredOn_contains": "2023-11-13T10:15",
            "dosageInstruction": [
                {
                    "route": "IV",
                    "doseAndRate": [
                        {
                            "doseQuantity": {"value": dose, "unit": "g"},
                            "rateQuantity": {"value": rate, "unit": "h"},
                        }
                    ],
                }
            ],
            "status": "active",
            "intent": "order",
            "subject": {"reference": f"Patient/{eval_mrn}"},
        }
    }


def _build_expected_task9_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    eval_mrn = row.get("eval_mrn")
    expected = _to_float(row.get("expected_answer"))
    if not isinstance(eval_mrn, str) or not eval_mrn or expected is None:
        return None
    dose = (3.5 - expected) / 0.1 * 10.0
    return {
        "medicationrequest_create": {
            "resourceType": "MedicationRequest",
            "medicationCodeableConcept": {
                "coding": [{"system": "http://hl7.org/fhir/sid/ndc", "code": "40032-917-01"}]
            },
            "authoredOn_contains": "2023-11-13T10:15",
            "dosageInstruction": [
                {"route": "oral", "doseAndRate": [{"doseQuantity": {"value": dose, "unit": "mEq"}}]}
            ],
            "status": "active",
            "intent": "order",
            "subject": {"reference": f"Patient/{eval_mrn}"},
        },
        "procedure_create": {
            "resourceType": "ServiceRequest",
            "code": {"coding": [{"system": "http://loinc.org", "code": "2823-3"}]},
            "authoredOn": "2023-11-13T10:15:00+00:00",
            "status": "active",
            "intent": "order",
            "priority": "stat",
            "subject": {"reference": f"Patient/{eval_mrn}"},
            "occurrenceDateTime_contains": "2023-11-14T08:",
        },
    }


def _build_expected_action_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    task_id = row.get("task_id")
    if not isinstance(task_id, str):
        return None
    group = task_id.split("_", 1)[0]
    if group == "task3":
        return _build_expected_task3_payload(row)
    if group == "task5":
        return _build_expected_task5_payload(row)
    if group == "task8":
        return _build_expected_task8_payload(row)
    if group == "task9":
        return _build_expected_task9_payload(row)
    return None


def _build_actual_action_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "vital_create": _extract_tool_resource(row, "vital_create"),
        "medicationrequest_create": _extract_tool_resource(row, "medicationrequest_create"),
        "procedure_create": _extract_tool_resource(row, "procedure_create"),
    }


def _build_query_case(detail: dict[str, Any]) -> dict[str, Any] | None:
    if detail.get("failure_kind") != "error_type":
        return None
    if detail.get("failure_reason") != "final_answer_mismatch":
        return None
    row = detail.get("row")
    if not isinstance(row, dict):
        return None
    if str(row.get("task_type")) != "query":
        return None
    task_id = row.get("task_id")
    if not isinstance(task_id, str):
        return None
    return {
        "case_type": "query_compare",
        "task_id": task_id,
        "expected_answer": row.get("expected_answer"),
        "final_answer": row.get("final_answer"),
    }


def _build_action_payload_case(detail: dict[str, Any]) -> dict[str, Any] | None:
    if detail.get("failure_kind") != "action_override":
        return None
    reason = str(detail.get("failure_reason"))
    if not reason.endswith("_payload_exception"):
        return None
    row = detail.get("row")
    if not isinstance(row, dict):
        return None
    if str(row.get("task_type")) != "action":
        return None
    task_id = row.get("task_id")
    if not isinstance(task_id, str):
        return None
    expected_payload = _build_expected_action_payload(row)
    if expected_payload is None:
        return None
    return {
        "case_type": "action_payload_compare",
        "task_id": task_id,
        "expected_payload": expected_payload,
        "actual_payload": _build_actual_action_payload(row),
    }


def _build_cases(
    failure_details: list[dict[str, Any]],
) -> tuple[dict[JudgeCaseType, list[dict[str, Any]]], dict[str, int]]:
    grouped: dict[JudgeCaseType, list[dict[str, Any]]] = {
        "query_compare": [],
        "action_payload_compare": [],
    }
    skipped: dict[str, int] = {}
    for detail in failure_details:
        query_case = _build_query_case(detail)
        if query_case is not None:
            grouped["query_compare"].append(query_case)
            continue
        action_case = _build_action_payload_case(detail)
        if action_case is not None:
            grouped["action_payload_compare"].append(action_case)
            continue
        key = f"skipped:{detail.get('failure_kind')}:{detail.get('failure_reason')}"
        skipped[key] = skipped.get(key, 0) + 1
    return grouped, skipped


def _judge_batch(
    *,
    case_type: JudgeCaseType,
    batch_cases: list[dict[str, Any]],
    config: LLMJudgeConfig,
) -> tuple[dict[str, bool], list[dict[str, Any]], str]:
    if config.backend != "azure_openai":
        raise ValueError(
            f"Unsupported llm judge backend: {config.backend}. Expected azure_openai."
        )
    if case_type == "query_compare":
        system = (
            "You evaluate query-task answers. "
            "Compare only expected_answer vs final_answer for semantic equivalence. "
            "Formatting differences alone should not fail. Return ONLY JSON."
        )
        instructions = (
            "For each case, output pass if final_answer is semantically equivalent to expected_answer, "
            "otherwise fail. Output JSON object with key 'judgments' as list of "
            "{task_id, verdict, confidence, reason}."
        )
    else:
        system = (
            "You evaluate action-task payloads. "
            "Compare only actual_payload against expected_payload requirements. "
            "Return ONLY JSON."
        )
        instructions = (
            "For each case, output pass if actual_payload satisfies expected_payload requirements, "
            "otherwise fail. Focus only on fields in expected_payload. "
            "Output JSON object with key 'judgments' as list of "
            "{task_id, verdict, confidence, reason}."
        )
    user = {"rubric_version": "v2", "case_type": case_type, "instructions": instructions, "cases": batch_cases}
    response = run_direct_chat_completion(
        model=config.model,
        api_version=config.api_version,
        endpoint_name=config.endpoint_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=True)},
        ],
        temperature=config.temperature,
    )
    message = response.choices[0].message
    content = message.content or ""
    payload = _extract_json_payload(content)
    judgments = _normalize_judgments(payload)
    decisions = {row["task_id"]: row["verdict"] == "pass" for row in judgments}
    return decisions, judgments, content


def _judge_batch_with_split_fallback(
    *,
    case_type: JudgeCaseType,
    batch_cases: list[dict[str, Any]],
    config: LLMJudgeConfig,
    batch_id: int,
) -> tuple[dict[str, bool], list[dict[str, Any]]]:
    try:
        decisions, judgments, raw_content = _judge_batch(
            case_type=case_type, batch_cases=batch_cases, config=config
        )
        records = [
            {
                "batch_id": batch_id,
                "case_type": case_type,
                "task_id": j["task_id"],
                "verdict": j["verdict"],
                "confidence": j["confidence"],
                "reason": j["reason"],
                "raw_response": raw_content,
            }
            for j in judgments
        ]
        return decisions, records
    except Exception as exc:  # noqa: BLE001
        if len(batch_cases) <= 1:
            task_id = str(batch_cases[0].get("task_id"))
            return {}, [
                {
                    "batch_id": batch_id,
                    "case_type": case_type,
                    "task_id": task_id,
                    "verdict": "error",
                    "confidence": "unknown",
                    "reason": f"judge_error: {exc}",
                    "raw_response": "",
                }
            ]
        mid = math.ceil(len(batch_cases) / 2)
        left = batch_cases[:mid]
        right = batch_cases[mid:]
        left_decisions, left_records = _judge_batch_with_split_fallback(
            case_type=case_type, batch_cases=left, config=config, batch_id=batch_id
        )
        right_decisions, right_records = _judge_batch_with_split_fallback(
            case_type=case_type, batch_cases=right, config=config, batch_id=batch_id
        )
        merged = dict(left_decisions)
        merged.update(right_decisions)
        return merged, left_records + right_records


def run_llm_judgment_batches(
    *,
    failure_details: list[dict[str, Any]],
    config: LLMJudgeConfig,
) -> tuple[dict[str, bool], list[dict[str, Any]], dict[str, Any]]:
    grouped_cases, skipped = _build_cases(failure_details)
    if config.max_cases is not None:
        remaining = config.max_cases
        query_cases = grouped_cases["query_compare"][:remaining]
        remaining -= len(query_cases)
        action_cases = grouped_cases["action_payload_compare"][: max(remaining, 0)]
        grouped_cases = {
            "query_compare": query_cases,
            "action_payload_compare": action_cases,
        }

    decisions: dict[str, bool] = {}
    artifacts: list[dict[str, Any]] = []
    considered_by_type = {
        "query_compare": len(grouped_cases["query_compare"]),
        "action_payload_compare": len(grouped_cases["action_payload_compare"]),
    }

    batch_counter = 0
    for case_type in ("query_compare", "action_payload_compare"):
        cases = grouped_cases[case_type]
        if not cases:
            continue
        total_batches = math.ceil(len(cases) / config.batch_size)
        if config.max_batches is not None:
            total_batches = min(total_batches, config.max_batches)
        for idx in range(total_batches):
            batch_counter += 1
            start = idx * config.batch_size
            end = start + config.batch_size
            batch_cases = cases[start:end]
            batch_decisions, batch_artifacts = _judge_batch_with_split_fallback(
                case_type=case_type,
                batch_cases=batch_cases,
                config=config,
                batch_id=batch_counter,
            )
            decisions.update(batch_decisions)
            artifacts.extend(batch_artifacts)

    stats = {
        "considered_by_type": considered_by_type,
        "skipped_by_reason": dict(sorted(skipped.items())),
    }
    return decisions, artifacts, stats


def build_expected_action_payload_for_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """Return strict expected action payload template for supported writing task groups."""
    return _build_expected_action_payload(row)


def build_actual_action_payload_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Extract normalized action payload from tool trace for supported write tools."""
    return _build_actual_action_payload(row)
