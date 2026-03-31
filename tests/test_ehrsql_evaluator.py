"""Unit tests for EHRSQL harbor_evaluator module."""

from __future__ import annotations

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ehrsql"))

from scripts.ehrsql.harbor_evaluator import (
    evaluate_submission_rows,
    post_process_sql,
)


class TestPostProcessSql:
    """Test SQL post-processing."""

    def test_null_passthrough(self):
        assert post_process_sql("null") == "null"

    def test_lowercases_sql(self):
        result = post_process_sql("SELECT COUNT(*) FROM patients")
        assert result == "select count(*) from patients"


class TestEvaluateSubmissionRows:
    """Test submission evaluation."""

    def test_evaluate_empty_submission(self):
        result = evaluate_submission_rows([], [], Path("/nonexistent"))
        assert result["pass_at_1"] == 0.0
        assert result["total_tasks"] == 0

    def test_evaluate_both_null(self):
        """Both predicted and gold are null — should pass."""
        submission = [{"task_id": "t1", "final_answer": "null"}]
        answer_key = [{"task_id": "t1", "expected_answer": "null", "db_id": "mimic_iii"}]

        result = evaluate_submission_rows(submission, answer_key, Path("/nonexistent"))
        assert result["total_tasks"] == 1
        assert result["passed_tasks"] == 1
        assert result["pass_at_1"] == 1.0

    def test_evaluate_result_structure(self):
        """Test that evaluation returns expected keys."""
        submission = [{"task_id": "t1", "final_answer": "SELECT 1"}]
        answer_key = [{"task_id": "t1", "expected_answer": "SELECT 1", "db_id": "mimic_iii"}]

        result = evaluate_submission_rows(submission, answer_key, Path("/nonexistent"))
        assert "pass_at_1" in result
        assert "total_tasks" in result
        assert "results" in result
        assert "precision_ans" in result
        assert "recall_ans" in result
        assert "f1_ans" in result
        assert "precision_exec" in result
        assert "recall_exec" in result
        assert "f1_exec" in result
