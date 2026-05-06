"""Evaluator for tumor_area_selection_pathology Harbor tasks."""

from __future__ import annotations

import json
from typing import Any


def _normalize_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        rows = payload["results"]
    else:
        raise ValueError("submission payload must be a list or an object with a 'results' list")
    return [dict(row) for row in rows if isinstance(row, dict)]


def load_submission_text(text: str) -> list[dict[str, Any]]:
    return _normalize_rows(json.loads(text))


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n", ""}:
            return False
    return False


def _tile_key(tile: dict[str, Any]) -> tuple[int, int]:
    return (int(tile.get("x", -1)), int(tile.get("y", -1)))


def _normalize_tile_set(value: Any) -> set[tuple[int, int]]:
    if not isinstance(value, list):
        return set()
    tiles: set[tuple[int, int]] = set()
    for row in value:
        if not isinstance(row, dict):
            continue
        x = row.get("x")
        y = row.get("y")
        if isinstance(x, int) and isinstance(y, int):
            tiles.add((x, y))
    return tiles


def evaluate_tcga_row(
    submission_row: dict[str, Any],
    answer_row: dict[str, Any],
) -> dict[str, Any]:
    expected = _normalize_bool(answer_row.get("expected_contains_tumor"))
    predicted = _normalize_bool(submission_row.get("contains_tumor"))
    correct = expected == predicted
    return {
        "subset": "tcga",
        "contains_tumor_correct": correct,
        "tile_precision": 0.0,
        "tile_recall": 0.0,
        "tile_f1": 0.0,
        "tumor_coverage": 0.0,
        "tp": 1 if predicted and expected else 0,
        "fp": 1 if predicted and not expected else 0,
        "fn": 1 if (not predicted) and expected else 0,
        "tn": 1 if (not predicted) and (not expected) else 0,
        "reward": 1.0 if correct else 0.0,
    }


def evaluate_camelyon_row(
    submission_row: dict[str, Any],
    answer_row: dict[str, Any],
) -> dict[str, Any]:
    predicted_tiles = _normalize_tile_set(submission_row.get("predicted_tumor_tiles"))
    gold_tiles = _normalize_tile_set(answer_row.get("expected_tumor_tiles"))

    tp = len(predicted_tiles & gold_tiles)
    fp = len(predicted_tiles - gold_tiles)
    fn = len(gold_tiles - predicted_tiles)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "subset": "camelyon16",
        "contains_tumor_correct": True,
        "tile_precision": precision,
        "tile_recall": recall,
        "tile_f1": f1,
        "tumor_coverage": 0.0,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": 0,
        "reward": f1,
    }


def evaluate_submission_rows(
    submission_rows: list[dict[str, Any]],
    answer_key_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    answers_by_id = {
        str(row.get("task_id", "")): row
        for row in answer_key_rows
        if isinstance(row, dict)
    }
    results: list[dict[str, Any]] = []
    for submission_row in submission_rows:
        task_id = str(submission_row.get("task_id", ""))
        answer_row = answers_by_id.get(task_id)
        if answer_row is None:
            results.append(
                {
                    "task_id": task_id,
                    "subset": "unknown",
                    "error": "missing_answer_key",
                    "reward": 0.0,
                }
            )
            continue
        subset = str(answer_row.get("subset", ""))
        if subset == "tcga":
            metrics = evaluate_tcga_row(submission_row, answer_row)
        elif subset == "camelyon16":
            metrics = evaluate_camelyon_row(submission_row, answer_row)
        else:
            raise ValueError(f"Unknown subset: {subset}")
        metrics["task_id"] = task_id
        results.append(metrics)

    total_reward = sum(float(row.get("reward", 0.0)) for row in results)
    return {
        "total_tasks": len(results),
        "avg_reward": total_reward / len(results) if results else 0.0,
        "results": results,
    }
