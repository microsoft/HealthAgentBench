"""Unit tests for EHRSQL normalization module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Import normalization functions
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ehrsql"))

from scripts.ehrsql.normalization import (
    build_harbor_answer_key,
    build_instruction,
    default_selected_task_ids,
    infer_db_id,
    infer_split,
    load_raw_tasks,
    normalize_harbor_task,
    select_tasks,
)


@pytest.fixture
def sample_ehrsql_task():
    """Sample EHRSQL task for testing."""
    return {
        "id": "task_001",
        "question": "What is the method of intake for clobetasol propionate?",
        "db_id": "mimic_iii",
        "split": "valid",
        "query": "SELECT DISTINCT route FROM prescriptions WHERE drug = 'clobetasol propionate'",
        "is_impossible": False,
        "importance": "medium",
    }


@pytest.fixture
def sample_unanswerable_task():
    """Sample unanswerable EHRSQL task."""
    return {
        "id": "task_002",
        "question": "What is an unanswerable question?",
        "db_id": "eicu",
        "split": "test",
        "query": "nan",
        "is_impossible": True,
        "importance": "low",
    }


class TestInferenceFunctions:
    """Test infer_* helper functions."""

    def test_infer_db_id(self, sample_ehrsql_task):
        """Test database ID inference."""
        assert infer_db_id(sample_ehrsql_task) == "mimic_iii"
        assert infer_db_id({"db_id": "eicu"}) == "eicu"
        assert infer_db_id({}) == "unknown"

    def test_infer_split(self, sample_ehrsql_task):
        """Test split inference."""
        assert infer_split(sample_ehrsql_task) == "valid"
        assert infer_split({"split": "test"}) == "test"
        assert infer_split({}) == "valid"


class TestInstructionBuilding:
    """Test instruction building."""

    def test_build_instruction_basic(self):
        """Test basic instruction formatting."""
        instr = build_instruction(base_question="What is X?", db_id="mimic_iii")
        assert "What is X?" in instr
        assert "MIMIC-III" in instr
        assert "sql" in instr.lower()

    def test_build_instruction_eicu(self):
        """Test instruction for eICU database."""
        instr = build_instruction(base_question="What is Y?", db_id="eicu")
        assert "What is Y?" in instr
        assert "eICU" in instr


class TestTaskNormalization:
    """Test task normalization functions."""

    def test_normalize_harbor_task(self, sample_ehrsql_task):
        """Test normalization of a single task."""
        normalized = normalize_harbor_task(sample_ehrsql_task, split="valid")

        assert normalized["task_id"].startswith("ehrsql_mimic_iii_valid_")
        assert normalized["instruction"]  # Non-empty
        assert normalized["final_answer"] == ""  # Agent-editable
        assert normalized["payload"] is None  # No payload for text-to-SQL

    def test_build_harbor_answer_key_answerable(self, sample_ehrsql_task):
        """Test answer key for answerable task."""
        key = build_harbor_answer_key(sample_ehrsql_task, split="valid")

        assert key["category"] == "factual_qa"
        assert key["difficulty"] == "medium"
        assert key["db_id"] == "mimic_iii"
        assert key["is_impossible"] is False
        assert key["expected_answer"] == sample_ehrsql_task["query"]

    def test_build_harbor_answer_key_unanswerable(self, sample_unanswerable_task):
        """Test answer key for unanswerable task."""
        key = build_harbor_answer_key(sample_unanswerable_task, split="test")

        assert key["category"] == "factual_qa"
        assert key["difficulty"] == "easy"  # Low importance -> easy
        assert key["is_impossible"] is True
        assert key["expected_answer"] == "null"

    def test_difficulty_mapping(self):
        """Test difficulty mapping from importance."""
        task_high = {"importance": "high"}
        key_high = build_harbor_answer_key(task_high, split="valid")
        assert key_high["difficulty"] == "hard"

        task_low = {"importance": "low"}
        key_low = build_harbor_answer_key(task_low, split="valid")
        assert key_low["difficulty"] == "easy"


class TestTaskSelection:
    """Test task selection functions."""

    def test_default_selected_task_ids(self, sample_ehrsql_task, sample_unanswerable_task):
        """Test default task selection strategy."""
        tasks = [sample_ehrsql_task, sample_unanswerable_task]
        selected = default_selected_task_ids(tasks)

        # Should select one task per (db, importance) combo
        assert len(selected) > 0
        assert all(isinstance(t_id, str) for t_id in selected)

    def test_select_tasks(self, sample_ehrsql_task, sample_unanswerable_task):
        """Test task filtering by ID."""
        tasks = [sample_ehrsql_task, sample_unanswerable_task]
        selected = select_tasks(tasks, ["task_001"])

        assert len(selected) == 1
        assert selected[0]["id"] == "task_001"

    def test_select_tasks_empty(self, sample_ehrsql_task):
        """Test selection with non-existent task IDs."""
        tasks = [sample_ehrsql_task]
        selected = select_tasks(tasks, ["nonexistent"])

        assert len(selected) == 0


class TestLoadRawTasks:
    """Test loading raw task JSON."""

    def test_load_raw_tasks_list(self, tmp_path):
        """Test loading JSON with list format."""
        test_json = tmp_path / "tasks.json"
        tasks = [{"id": "t1", "question": "Q1"}, {"id": "t2", "question": "Q2"}]
        test_json.write_text(json.dumps(tasks))

        loaded = load_raw_tasks(test_json)
        assert len(loaded) == 2
        assert loaded[0]["id"] == "t1"

    def test_load_raw_tasks_dict_with_tasks_key(self, tmp_path):
        """Test loading JSON with dict containing 'tasks' key."""
        test_json = tmp_path / "tasks.json"
        data = {"tasks": [{"id": "t1"}, {"id": "t2"}]}
        test_json.write_text(json.dumps(data))

        loaded = load_raw_tasks(test_json)
        assert len(loaded) == 2

    def test_load_raw_tasks_invalid(self, tmp_path):
        """Test loading invalid JSON format."""
        test_json = tmp_path / "tasks.json"
        test_json.write_text(json.dumps({"invalid": "format"}))

        with pytest.raises(ValueError):
            load_raw_tasks(test_json)
