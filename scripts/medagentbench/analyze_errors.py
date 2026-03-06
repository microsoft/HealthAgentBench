#!/usr/bin/env python3
"""Analyze failed MedAgentBench cases and print concise diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.medagentbench.evaluator import get_strict_failure_details
from scripts.medagentbench.llm_judge_batch import (
    build_actual_action_payload_for_row,
    build_expected_action_payload_for_row,
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _clip(text: str, max_width: int) -> str:
    if len(text) <= max_width:
        return text
    if max_width <= 7:
        return text[: max_width - 3] + "..."
    head = (max_width - 3) // 2
    tail = max_width - 3 - head
    return f"{text[:head]}...{text[-tail:]}"


def _scalar_equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) <= 1e-6
    return expected == actual


def _collect_payload_diffs(
    expected: Any,
    actual: Any,
    *,
    path: str = "",
    diffs: list[str] | None = None,
    limit: int = 8,
) -> list[str]:
    if diffs is None:
        diffs = []
    if len(diffs) >= limit:
        return diffs

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            diffs.append(f"{path or '$'}: expected object, got {type(actual).__name__}")
            return diffs
        for key, expected_val in expected.items():
            if len(diffs) >= limit:
                break
            if key.endswith("_contains"):
                actual_key = key.removesuffix("_contains")
                value = actual.get(actual_key)
                if expected_val not in str(value):
                    diffs.append(
                        f"{path + '.' if path else ''}{actual_key}: expected contains {expected_val!r}, got {value!r}"
                    )
                continue
            if key not in actual:
                diffs.append(f"{path + '.' if path else ''}{key}: missing")
                continue
            _collect_payload_diffs(
                expected_val,
                actual[key],
                path=f"{path + '.' if path else ''}{key}",
                diffs=diffs,
                limit=limit,
            )
        return diffs

    if isinstance(expected, list):
        if not isinstance(actual, list):
            diffs.append(f"{path or '$'}: expected list, got {type(actual).__name__}")
            return diffs
        if len(actual) < len(expected):
            diffs.append(f"{path or '$'}: expected len>={len(expected)}, got {len(actual)}")
            return diffs
        for idx, expected_item in enumerate(expected):
            if len(diffs) >= limit:
                break
            _collect_payload_diffs(
                expected_item,
                actual[idx],
                path=f"{path}[{idx}]",
                diffs=diffs,
                limit=limit,
            )
        return diffs

    if not _scalar_equal(expected, actual):
        diffs.append(f"{path or '$'}: expected {expected!r}, got {actual!r}")
    return diffs


def _summarize_action_payload(row: dict[str, Any]) -> str:
    expected = build_expected_action_payload_for_row(row)
    if expected is None:
        return "unsupported task group for expected payload"
    actual = build_actual_action_payload_for_row(row)
    diffs = _collect_payload_diffs(expected, actual)
    if not diffs:
        return "no mismatch found (likely policy/ordering issue)"
    return " | ".join(diffs[:4])


def _tool_summary(row: dict[str, Any]) -> str:
    trace = row.get("tool_trace")
    if not isinstance(trace, list):
        return ""
    names: list[str] = []
    for entry in trace:
        if not isinstance(entry, dict):
            continue
        tool = entry.get("tool")
        if isinstance(tool, str):
            names.append(tool)
    return ",".join(names)


def _llm_pass_task_ids(results_path: Path) -> set[str]:
    judgments_path = results_path.parent / "llm_judgments.jsonl"
    passed: set[str] = set()
    for row in _load_jsonl(judgments_path):
        if row.get("verdict") == "pass" and isinstance(row.get("task_id"), str):
            passed.add(row["task_id"])
    return passed


def _build_rows(results_path: Path, fail_mode: str) -> list[dict[str, str]]:
    strict_failures = get_strict_failure_details(str(results_path))
    if fail_mode == "llm":
        llm_passed = _llm_pass_task_ids(results_path)
        selected = [entry for entry in strict_failures if entry["task_id"] not in llm_passed]
    else:
        selected = strict_failures

    rows: list[dict[str, str]] = []
    for entry in selected:
        row = entry["row"]
        task_type = str(row.get("task_type", ""))
        base = {
            "task_id": str(row.get("task_id", "")),
            "task_type": task_type,
            "category": str(row.get("category", "")),
            "difficulty": str(row.get("difficulty", "")),
            "error_type": str(row.get("error_type", "")),
            "failure_reason": str(entry.get("failure_reason", "")),
            "tools": _tool_summary(row),
            "expected_answer": "",
            "final_answer": "",
            "payload_issue": "",
        }
        if task_type == "query":
            base["expected_answer"] = str(row.get("expected_answer", ""))
            base["final_answer"] = str(row.get("final_answer", ""))
        else:
            base["payload_issue"] = _summarize_action_payload(row)
        rows.append(base)
    return rows


def _print_table(rows: list[dict[str, str]], *, max_rows: int, max_col_width: int) -> None:
    columns = [
        "task_id",
        "task_type",
        "category",
        "difficulty",
        "failure_reason",
        "expected_answer",
        "final_answer",
        "payload_issue",
    ]
    shown = rows[:max_rows]
    widths: dict[str, int] = {col: len(col) for col in columns}
    for row in shown:
        for col in columns:
            widths[col] = min(max(widths[col], len(_clip(row[col], max_col_width))), max_col_width)

    header = " | ".join(col.ljust(widths[col]) for col in columns)
    sep = "-+-".join("-" * widths[col] for col in columns)
    print(header)
    print(sep)
    for row in shown:
        print(
            " | ".join(
                _clip(row[col], max_col_width).ljust(widths[col]) for col in columns
            )
        )
    if len(rows) > max_rows:
        print(f"... showing {max_rows}/{len(rows)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze MedAgentBench failed cases.")
    parser.add_argument("--results", required=True, help="Path to results.jsonl")
    parser.add_argument(
        "--fail-mode",
        choices=["strict", "llm"],
        default="strict",
        help="Which failure set to analyze: strict failures or failures after llm overrides.",
    )
    parser.add_argument("--max-rows", type=int, default=50)
    parser.add_argument("--max-col-width", type=int, default=60)
    parser.add_argument("--format", choices=["table", "json"], default="json")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path. If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    results_path = Path(args.results)
    rows = _build_rows(results_path, args.fail_mode)
    clipped_rows: list[dict[str, str]] = []
    for row in rows[: args.max_rows]:
        clipped_rows.append(
            {key: _clip(str(value), args.max_col_width) for key, value in row.items()}
        )

    if args.format == "json":
        payload = {
            "fail_mode": args.fail_mode,
            "results_path": str(results_path),
            "shown_rows": len(clipped_rows),
            "total_failed_rows": len(rows),
            "rows": clipped_rows,
        }
        text = json.dumps(payload, indent=2, ensure_ascii=True)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text + "\n", encoding="utf-8")
            print(f"wrote {output_path}")
            return
        print(text)
        return
    _print_table(clipped_rows, max_rows=args.max_rows, max_col_width=args.max_col_width)


if __name__ == "__main__":
    main()
