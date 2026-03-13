from scripts.medagentbench.harbor_evaluator import evaluate_submission_rows


def test_harbor_evaluator_passes_query_and_payload_cases():
    rows = [
        {
            "id": "task1_1",
            "sol": ["S1234567"],
            "final_answer": "S1234567",
            "payload": None,
        },
        {
            "id": "task3_1",
            "eval_MRN": "S2380121",
            "final_answer": "",
            "payload": {
                "resourceType": "Observation",
                "status": "final",
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
                "valueString": "118/77 mmHg",
                "subject": {"reference": "Patient/S2380121"},
            },
        },
    ]

    summary = evaluate_submission_rows(rows)
    assert summary["total_tasks"] == 2
    assert summary["passed_tasks"] == 2
    assert summary["pass_at_1"] == 1.0


def test_harbor_evaluator_handles_multi_payload_and_optional_noop_cases():
    rows = [
        {
            "id": "task5_1",
            "eval_MRN": "S6315806",
            "sol": [-1],
            "final_answer": -1,
            "payload": None,
        },
        {
            "id": "task9_1",
            "eval_MRN": "S3241217",
            "sol": [3.2],
            "final_answer": 3.2,
            "payload": [
                {
                    "resourceType": "MedicationRequest",
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://hl7.org/fhir/sid/ndc",
                                "code": "40032-917-01",
                            }
                        ]
                    },
                    "authoredOn": "2023-11-13T10:15:00+00:00",
                    "dosageInstruction": [
                        {
                            "route": "oral",
                            "doseAndRate": [
                                {
                                    "doseQuantity": {"value": 30.0, "unit": "mEq"},
                                }
                            ],
                        }
                    ],
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/S3241217"},
                },
                {
                    "resourceType": "ServiceRequest",
                    "code": {
                        "coding": [
                            {"system": "http://loinc.org", "code": "2823-3"}
                        ]
                    },
                    "authoredOn": "2023-11-13T10:15:00+00:00",
                    "status": "active",
                    "intent": "order",
                    "priority": "stat",
                    "subject": {"reference": "Patient/S3241217"},
                    "occurrenceDateTime": "2023-11-14T08:00:00+00:00",
                },
            ],
        },
    ]

    summary = evaluate_submission_rows(rows)
    assert summary["passed_tasks"] == 2


def test_harbor_evaluator_requires_task10_payload_when_order_needed():
    rows = [
        {
            "id": "task10_1",
            "eval_MRN": "S6227720",
            "sol": [-1],
            "final_answer": [-1],
            "payload": None,
        }
    ]

    summary = evaluate_submission_rows(rows)
    assert summary["passed_tasks"] == 0
    assert summary["error_taxonomy"]["payload_mismatch"] == 1
