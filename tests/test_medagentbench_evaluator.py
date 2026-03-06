import json
from pathlib import Path

from scripts.medagentbench.evaluator import evaluate_results


def test_evaluate_results_computes_metrics(tmp_path: Path):
    results = [
        {
            "task_id": "a",
            "category": "factual_qa",
            "task_type": "query",
            "success": True,
        },
        {
            "task_id": "b",
            "category": "factual_qa",
            "task_type": "query",
            "success": False,
            "error_type": "final_answer_mismatch",
        },
        {
            "task_id": "c",
            "category": "care_ordering",
            "task_type": "action",
            "success": False,
            "error_type": "tool_or_runtime_error",
        },
    ]
    path = tmp_path / "results.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row) + "\n")

    summary = evaluate_results(str(path))
    assert summary["total_tasks"] == 3
    assert abs(summary["pass_at_1"] - (1 / 3)) < 1e-9
    assert summary["by_category"]["factual_qa"]["total"] == 2
    assert summary["query_vs_action"]["action"]["total"] == 1
    assert summary["error_taxonomy"]["tool_or_runtime_error"] == 1


def test_evaluate_results_overrides_action_success_from_trace(tmp_path: Path):
    results = [
        {
            "task_id": "task3_1",
            "category": "clinical_data_recording",
            "task_type": "action",
            "success": False,
            "error_type": "final_answer_mismatch",
            "eval_mrn": "S123",
            "tool_trace": [
                {
                    "tool": "vital_create",
                    "args": {
                        "resource": {
                            "resourceType": "Observation",
                            "category": {
                                "coding": [
                                    {
                                        "system": "http://hl7.org/fhir/observation-category",
                                        "code": "vital-signs",
                                        "display": "Vital Signs",
                                    }
                                ]
                            },
                            "code": {"text": "BP"},
                            "effectiveDateTime": "2023-11-13T10:15:00+00:00",
                            "status": "final",
                            "valueString": "118/77 mmHg",
                            "subject": {"reference": "Patient/S123"},
                        }
                    },
                    "status": "skipped_evaluation_mode",
                }
            ],
        },
        {
            "task_id": "task8_1",
            "category": "care_ordering",
            "task_type": "action",
            "success": False,
            "error_type": "final_answer_mismatch",
            "eval_mrn": "S456",
            "tool_trace": [
                {
                    "tool": "procedure_create",
                    "args": {
                        "resource": {
                            "resourceType": "ServiceRequest",
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "306181000000106",
                                    }
                                ]
                            },
                            "authoredOn": "2023-11-13T10:15:00+00:00",
                            "status": "active",
                            "intent": "order",
                            "priority": "stat",
                            "note": [
                                {
                                    "text": (
                                        "Situation: acute left knee injury, Background: radiology report "
                                        "indicates ACL tear. Assessment: ACL tear grade II. "
                                        "Recommendation: request for Orthopedic service to evaluate and "
                                        "provide management recommendations."
                                    )
                                }
                            ],
                            "subject": {"reference": "Patient/S456"},
                        }
                    },
                    "status": "skipped_evaluation_mode",
                }
            ],
        },
    ]
    path = tmp_path / "results.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row) + "\n")

    summary = evaluate_results(str(path))
    assert summary["total_tasks"] == 2
    assert summary["passed_tasks"] == 2
    assert summary["pass_at_1"] == 1.0
    assert summary["action_override"]["total"] == 2
    assert summary["action_override"]["passed"] == 2


def test_evaluate_results_marks_invalid_action_trace(tmp_path: Path):
    results = [
        {
            "task_id": "task3_2",
            "category": "clinical_data_recording",
            "task_type": "action",
            "success": True,
            "error_type": None,
            "eval_mrn": "S123",
            "tool_trace": [
                {
                    "tool": "vital_create",
                    "args": {"resource": {"resourceType": "Observation"}},
                    "status": "skipped_evaluation_mode",
                }
            ],
        }
    ]
    path = tmp_path / "results.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row) + "\n")

    summary = evaluate_results(str(path))
    assert summary["total_tasks"] == 1
    assert summary["passed_tasks"] == 0
    assert summary["error_taxonomy"]["action_trace_validation_failed"] == 1
