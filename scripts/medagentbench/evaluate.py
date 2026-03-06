#!/usr/bin/env python3
"""Benchmark evaluation CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.medagentbench.evaluator import evaluate_results, get_strict_failure_details
from scripts.medagentbench.llm_judge_batch import LLMJudgeConfig, run_llm_judgment_batches


def _to_markdown(summary: dict) -> str:
    lines = [
        "# MedAgentBench Evaluation Summary",
        "",
        f"- pass@1: {summary['pass_at_1']:.4f}",
        f"- total_tasks: {summary['total_tasks']}",
        f"- passed_tasks: {summary.get('passed_tasks', 0)}",
        "",
        "## By Category",
        "",
        "| category | total | passed | pass@1 |",
        "|---|---:|---:|---:|",
    ]
    for key, value in summary["by_category"].items():
        lines.append(f"| {key} | {value['total']} | {value['passed']} | {value['pass_at_1']:.4f} |")

    lines.extend([
        "",
        "## Query vs Action",
        "",
        "| type | total | passed | pass@1 |",
        "|---|---:|---:|---:|",
    ])
    for key, value in summary["query_vs_action"].items():
        lines.append(f"| {key} | {value['total']} | {value['passed']} | {value['pass_at_1']:.4f} |")

    lines.extend([
        "",
        "## Error Taxonomy",
        "",
        "| error_type | count |",
        "|---|---:|",
    ])
    for key, value in summary["error_taxonomy"].items():
        lines.append(f"| {key} | {value} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument(
        "--action-eval-mode",
        choices=["strict", "llm_assisted"],
        default="strict",
        help="How to evaluate results: strict rules or llm-assisted strict-failure adjudication.",
    )
    parser.add_argument("--llm-judge-model", default="o4-mini")
    parser.add_argument("--llm-judge-backend", default="azure_openai")
    parser.add_argument("--llm-judge-api-version", default="2025-03-01-preview")
    parser.add_argument("--llm-judge-endpoint-name", default="hanover-openai-east")
    parser.add_argument("--llm-judge-temperature", type=float, default=0.0)
    parser.add_argument("--llm-judge-max-cases", type=int, default=None)
    parser.add_argument("--llm-judge-batch-size", type=int, default=20)
    parser.add_argument("--llm-judge-max-batches", type=int, default=None)
    args = parser.parse_args()

    if args.task != "medagentbench":
        raise SystemExit("Only --task medagentbench is supported in this milestone.")

    results_path = Path(args.results)
    if args.action_eval_mode == "strict":
        summary = evaluate_results(str(results_path))
    else:
        strict_summary = evaluate_results(str(results_path))
        strict_failures = get_strict_failure_details(str(results_path))
        strict_failed_ids = {entry["task_id"] for entry in strict_failures}
        judge_config = LLMJudgeConfig(
            model=args.llm_judge_model,
            backend=args.llm_judge_backend,
            api_version=args.llm_judge_api_version,
            endpoint_name=args.llm_judge_endpoint_name,
            temperature=args.llm_judge_temperature,
            max_cases=args.llm_judge_max_cases,
            batch_size=args.llm_judge_batch_size,
            max_batches=args.llm_judge_max_batches,
        )
        decisions, artifacts, judge_stats = run_llm_judgment_batches(
            failure_details=strict_failures,
            config=judge_config,
        )
        summary = evaluate_results(
            str(results_path),
            success_overrides=decisions,
        )
        summary["llm_override"].update(
            {
                "mode": "llm_assisted",
                "strict_failed_total": len(strict_failed_ids),
                "considered": len(decisions),
                "model": args.llm_judge_model,
                "backend": args.llm_judge_backend,
                "api_version": args.llm_judge_api_version,
                "endpoint_name": args.llm_judge_endpoint_name,
                "batch_size": args.llm_judge_batch_size,
                "considered_by_type": judge_stats.get("considered_by_type", {}),
                "skipped_by_reason": judge_stats.get("skipped_by_reason", {}),
            }
        )
        summary["strict_baseline"] = {
            "pass_at_1": strict_summary["pass_at_1"],
            "passed_tasks": strict_summary["passed_tasks"],
            "total_tasks": strict_summary["total_tasks"],
        }

    out_dir = results_path.parent
    summary_json_path = out_dir / "summary.json"
    summary_md_path = out_dir / "summary.md"
    llm_judgments_path = out_dir / "llm_judgments.jsonl"

    summary_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary_md_path.write_text(_to_markdown(summary), encoding="utf-8")
    if args.action_eval_mode == "llm_assisted":
        with llm_judgments_path.open("w", encoding="utf-8") as f:
            for row in artifacts:
                f.write(json.dumps(row, ensure_ascii=True) + "\n")

    print(json.dumps({"summary_json": str(summary_json_path), "summary_md": str(summary_md_path), **summary}))


if __name__ == "__main__":
    main()
