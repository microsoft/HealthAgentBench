#!/usr/bin/env python3
"""Top-level experiment runner for MedAgentBench tasks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ehr_co_scientist.agent import AgentConfig, run_task
from ehr_co_scientist.backends.adapter import BackendConfig
from ehr_co_scientist.tools.catalog import TOOL_DEFINITIONS
from ehr_co_scientist.tools.fhir_tools import FHIRClient
from ehr_co_scientist.tools.tooling.function_tools import get_openai_function_tools
from ehr_co_scientist.tools.tooling.runtime import ToolRuntime


def _now_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_manifest_tasks(task_root: Path, split: str) -> list[dict[str, Any]]:
    manifests = sorted(task_root.glob(f"*/sources/medagentbench/{split}.yaml"))
    all_tasks: list[dict[str, Any]] = []
    for manifest in manifests:
        payload = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        task_rows = payload.get("tasks", [])
        for row in task_rows:
            if isinstance(row, dict):
                item = dict(row)
                item.setdefault("manifest_path", str(manifest))
                all_tasks.append(item)
    return sorted(all_tasks, key=lambda t: str(t.get("task_id", "")))


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_selector(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _apply_selector(
    tasks: list[dict[str, Any]], selector: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    include = selector.get("include", {}) if isinstance(selector, dict) else {}
    exclude = selector.get("exclude", {}) if isinstance(selector, dict) else {}

    include_ids = set(include.get("task_ids", []) or [])
    include_categories = set(include.get("categories", []) or [])
    include_difficulties = set(include.get("difficulties", []) or [])
    include_types = set(include.get("task_types", []) or [])

    exclude_ids = set(exclude.get("task_ids", []) or [])
    exclude_categories = set(exclude.get("categories", []) or [])
    exclude_difficulties = set(exclude.get("difficulties", []) or [])
    exclude_types = set(exclude.get("task_types", []) or [])

    stats = {
        "excluded_by_id": 0,
        "excluded_by_category": 0,
        "excluded_by_difficulty": 0,
        "excluded_by_type": 0,
    }

    def included(task: dict[str, Any]) -> bool:
        if include_ids and task.get("task_id") not in include_ids:
            return False
        if include_categories and task.get("category") not in include_categories:
            return False
        if include_difficulties and task.get("difficulty") not in include_difficulties:
            return False
        if include_types and task.get("task_type") not in include_types:
            return False
        return True

    selected: list[dict[str, Any]] = []
    for task in tasks:
        if not included(task):
            continue
        if task.get("task_id") in exclude_ids:
            stats["excluded_by_id"] += 1
            continue
        if task.get("category") in exclude_categories:
            stats["excluded_by_category"] += 1
            continue
        if task.get("difficulty") in exclude_difficulties:
            stats["excluded_by_difficulty"] += 1
            continue
        if task.get("task_type") in exclude_types:
            stats["excluded_by_type"] += 1
            continue
        selected.append(task)

    return selected, stats


def _expected_match(expected: Any, predicted: str) -> bool:
    if expected in (None, ""):
        return False
    if isinstance(expected, list):
        expected_set = {str(x).strip().lower() for x in expected}
        return predicted.strip().lower() in expected_set
    return str(expected).strip().lower() == predicted.strip().lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--split", default="std")
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--backend", default="azure_openai")
    parser.add_argument("--model", default="gpt-5.2")
    parser.add_argument("--fhir-base-url", default="http://localhost:8080/fhir")
    parser.add_argument("--task-ids")
    parser.add_argument("--task-categories")
    parser.add_argument("--task-selector-file")
    parser.add_argument("--endpoint-name")
    parser.add_argument("--api-version", default="2025-03-01-preview")
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--evaluation-mode",
        action="store_true",
        help=(
            "Do not execute write tools in evaluation mode; terminate task early "
            "when a write tool is called."
        ),
    )
    args = parser.parse_args()

    if args.task != "medagentbench":
        raise SystemExit("Only --task medagentbench is supported in this milestone.")

    task_root = Path("tasks")
    all_tasks = _load_manifest_tasks(task_root=task_root, split=args.split)

    resolved_selector = {
        "split": args.split,
        "task_ids": _split_csv(args.task_ids),
        "task_categories": _split_csv(args.task_categories),
        "task_selector_file": args.task_selector_file,
    }

    selected = all_tasks

    # Precedence 1: explicit task IDs
    explicit_ids = set(_split_csv(args.task_ids))
    if explicit_ids:
        selected = [t for t in selected if t.get("task_id") in explicit_ids]

    # Precedence 2: selector file
    selector_stats: dict[str, int] = {}
    selector_path = Path(args.task_selector_file) if args.task_selector_file else None
    if selector_path is not None:
        selected, selector_stats = _apply_selector(
            selected, _load_selector(selector_path)
        )

    # Precedence 3: category filters
    categories = set(_split_csv(args.task_categories))
    if categories:
        selected = [t for t in selected if t.get("category") in categories]

    # Precedence 4 is split base set (already done by manifest load)

    # Precedence 5: max tasks
    if args.max_tasks is not None:
        selected = selected[: args.max_tasks]

    run_id = _now_run_id()
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("experiments/results/medagentbench") / run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    results_path = output_dir / "results.jsonl"
    metadata_path = output_dir / "run_metadata.json"

    backend_config = BackendConfig(
        backend=args.backend,
        model=args.model,
        endpoint_name=args.endpoint_name,
        api_version=args.api_version,
    )
    tool_runtime = ToolRuntime(fhir=FHIRClient(base_url=args.fhir_base_url))

    with results_path.open("w", encoding="utf-8") as out:
        for task in selected:
            task_id = str(task.get("task_id", ""))
            error_type: str | None = None
            task_allowed_tools = list(task.get("allowed_tools", []) or [])
            allowed_tool_set = set(task_allowed_tools) if task_allowed_tools else None
            chat_kwargs: dict[str, Any] = {}
            if task_allowed_tools:
                chat_kwargs = {
                    "tools": get_openai_function_tools(
                        TOOL_DEFINITIONS, task_allowed_tools
                    ),
                    "tool_choice": "auto",
                    "parallel_tool_calls": False,
                }
            try:
                agent_result = run_task(
                    task=task,
                    backend_config=backend_config,
                    tool_runtime=tool_runtime,
                    config=AgentConfig(
                        max_rounds=8,
                        evaluation_mode=args.evaluation_mode,
                    ),
                    chat_kwargs=chat_kwargs if chat_kwargs else None,
                    allowed_tools=allowed_tool_set,
                )
                final_answer = str(agent_result.get("final_answer", ""))
                error_text = agent_result.get("error")
                if error_text:
                    error_type = "tool_or_runtime_error"
            except Exception as exc:  # noqa: BLE001
                final_answer = ""
                agent_result = {"tool_trace": [], "rounds_used": 0, "error": str(exc)}
                error_type = "runtime_exception"

            success = _expected_match(task.get("expected_answer"), final_answer)
            if not success and error_type is None:
                error_type = "final_answer_mismatch"

            row = {
                "task_id": task_id,
                "category": task.get("category"),
                "task_type": task.get("task_type"),
                "difficulty": task.get("difficulty"),
                "instruction": task.get("instruction"),
                "expected_answer": task.get("expected_answer"),
                "final_answer": final_answer,
                "success": success,
                "tool_trace": agent_result.get("tool_trace", []),
                "rounds_used": agent_result.get("rounds_used", 0),
                "error_type": error_type,
                "terminated_early": bool(agent_result.get("terminated_early", False)),
                "termination_reason": agent_result.get("termination_reason"),
                "allowed_tools": task_allowed_tools,
                "backend": {
                    "backend": backend_config.backend,
                    "model": backend_config.model,
                    "endpoint_name": backend_config.endpoint_name,
                    "api_version": backend_config.api_version,
                },
            }
            out.write(json.dumps(row, ensure_ascii=True) + "\n")

    metadata = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resolved_selector": resolved_selector,
        "selector_stats": selector_stats,
        "task_count": len(selected),
        "backend_config": asdict(backend_config),
        "evaluation_mode": args.evaluation_mode,
        "enforce_allowed_tools": True,
        "fhir_base_url": args.fhir_base_url,
        "results_path": str(results_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "run_id": run_id,
                "results": str(results_path),
                "metadata": str(metadata_path),
            }
        )
    )


if __name__ == "__main__":
    main()
