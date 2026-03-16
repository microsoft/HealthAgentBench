"""Unit tests for EHRSQL harbor_evaluator module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ehrsql"))

from scripts.ehrsql.harbor_evaluator import (
    _compare_result_sets,
    _normalize_result_set,
    evaluate_submission_rows,
)


class TestNormalizeResultSet:
    """Test result set normalization."""

    def test_normalize_success_result(self):
        """Test normalizing a successful result."""
        result = {
            "status": "success",
            "row_count": 2,
            "columns": ["name", "age"],
            "rows": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ],
        }

        normalized = _normalize_result_set(result)
        assert normalized is not None
        assert len(normalized) == 2
        assert ("Alice", 30) in normalized
        assert ("Bob", 25) in normalized

    def test_normalize_null_result(self):
        """Test normalizing a null (unanswerable) result."""
        result = {"status": "null", "row_count": 0, "columns": [], "rows": []}

        normalized = _normalize_result_set(result)
        assert normalized is None

    def test_normalize_error_result(self):
        """Test normalizing an error result."""
        result = {"status": "error", "error": "SQL syntax error"}

        normalized = _normalize_result_set(result)
        assert normalized is None

    def test_normalize_empty_result(self):
        """Test normalizing an empty result set."""
        result = {
            "status": "success",
            "row_count": 0,
            "columns": ["id", "name"],
            "rows": [],
        }

        normalized = _normalize_result_set(result)
        assert normalized == set()

    def test_normalize_with_none_values(self):
        """Test normalizing result with None values."""
        result = {
            "status": "success",
            "row_count": 2,
            "columns": ["id", "value"],
            "rows": [
                {"id": 1, "value": None},
                {"id": 2, "value": "test"},
            ],
        }

        normalized = _normalize_result_set(result)
        assert normalized is not None
        assert (1, None) in normalized
        assert (2, "test") in normalized


class TestCompareResultSets:
    """Test result set comparison."""

    def test_compare_identical_results(self):
        """Test comparing identical result sets."""
        result1 = {
            "status": "success",
            "columns": ["name"],
            "rows": [{"name": "Alice"}],
        }
        result2 = {
            "status": "success",
            "columns": ["name"],
            "rows": [{"name": "Alice"}],
        }

        success, reason = _compare_result_sets(result1, result2)
        assert success is True
        assert reason == "match"

    def test_compare_different_results(self):
        """Test comparing different result sets."""
        result1 = {
            "status": "success",
            "columns": ["name"],
            "rows": [{"name": "Alice"}],
        }
        result2 = {
            "status": "success",
            "columns": ["name"],
            "rows": [{"name": "Bob"}],
        }

        success, reason = _compare_result_sets(result1, result2)
        assert success is False
        assert reason == "result_mismatch"

    def test_compare_both_null(self):
        """Test comparing two null results (unanswerable)."""
        result1 = {"status": "null"}
        result2 = {"status": "null"}

        success, reason = _compare_result_sets(result1, result2)
        assert success is True
        assert reason == "both_null"

    def test_compare_answerability_mismatch(self):
        """Test when one is null and one is answerable."""
        result1 = {"status": "null"}
        result2 = {
            "status": "success",
            "columns": ["x"],
            "rows": [{"x": 1}],
        }

        success, reason = _compare_result_sets(result1, result2)
        assert success is False
        assert reason == "answerability_mismatch"

    def test_compare_gold_error(self):
        """Test when gold result is an error."""
        result1 = {"status": "error", "error": "Database error"}
        result2 = {
            "status": "success",
            "columns": ["x"],
            "rows": [{"x": 1}],
        }

        success, reason = _compare_result_sets(result1, result2)
        assert success is False
        assert reason == "gold_error"

    def test_compare_pred_error(self):
        """Test when predicted result is an error."""
        result1 = {
            "status": "success",
            "columns": ["x"],
            "rows": [{"x": 1}],
        }
        result2 = {"status": "error", "error": "SQL syntax error"}

        success, reason = _compare_result_sets(result1, result2)
        assert success is False
        assert reason == "execution_error"

    def test_compare_unordered_results(self):
        """Test that result order doesn't matter (set-based comparison)."""
        result1 = {
            "status": "success",
            "columns": ["id"],
            "rows": [{"id": 1}, {"id": 2}],
        }
        result2 = {
            "status": "success",
            "columns": ["id"],
            "rows": [{"id": 2}, {"id": 1}],
        }

        success, reason = _compare_result_sets(result1, result2)
        assert success is True
        assert reason == "match"

    def test_compare_duplicate_rows(self):
        """Test that duplicate rows matter in comparison."""
        result1 = {
            "status": "success",
            "columns": ["id"],
            "rows": [{"id": 1}, {"id": 1}],
        }
        result2 = {
            "status": "success",
            "columns": ["id"],
            "rows": [{"id": 1}],
        }

        success, reason = _compare_result_sets(result1, result2)
        # Sets don't preserve duplicates, so they should match
        # This is a known limitation of set-based comparison
        assert success is True


class TestEvaluateSubmissionRows:
    """Test submission evaluation (requires mocking or fixtures)."""

    def test_evaluate_empty_submission(self):
        """Test evaluating an empty submission."""
        submission = []
        answer_key = []

        # This will likely fail due to missing DB, but test the logic
        # In real usage, db_dir would point to actual SQLite files
        result = evaluate_submission_rows(submission, answer_key, Path("/nonexistent"))

        assert result["pass_at_1"] == 0.0
        assert result["total_tasks"] == 0

    def test_evaluate_submission_structure(self):
        """Test that evaluation returns correct structure."""
        submission = [
            {
                "task_id": "test_1",
                "final_answer": "null",
            }
        ]
        answer_key = [
            {
                "task_id": "test_1",
                "expected_answer": "null",
                "db_id": "mimic_iii",
            }
        ]

        # With nonexistent DB, this will show errors in results
        result = evaluate_submission_rows(submission, answer_key, Path("/nonexistent"))

        assert "pass_at_1" in result
        assert "total_tasks" in result
        assert "error_taxonomy" in result
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_evaluate_result_keys(self):
        """Test that individual results have expected keys."""
        submission = [
            {
                "task_id": "test_1",
                "final_answer": "SELECT 1",
            }
        ]
        answer_key = [
            {
                "task_id": "test_1",
                "expected_answer": "SELECT 1",
                "db_id": "mimic_iii",
            }
        ]

        result = evaluate_submission_rows(submission, answer_key, Path("/nonexistent"))

        assert len(result["results"]) >= 1
        result_row = result["results"][0]
        assert "task_id" in result_row
        assert "success" in result_row
        assert "reason" in result_row
