import json
from pathlib import Path

from benchmarks.medagentbench.evaluator import evaluate_results


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
