#!/usr/bin/env python3
"""Benchmark evaluation CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.medagentbench.evaluator import evaluate_results


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
    args = parser.parse_args()

    if args.task != "medagentbench":
        raise SystemExit("Only --task medagentbench is supported in this milestone.")

    results_path = Path(args.results)
    summary = evaluate_results(str(results_path))

    out_dir = results_path.parent
    summary_json_path = out_dir / "summary.json"
    summary_md_path = out_dir / "summary.md"

    summary_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary_md_path.write_text(_to_markdown(summary), encoding="utf-8")

    print(json.dumps({"summary_json": str(summary_json_path), "summary_md": str(summary_md_path), **summary}))


if __name__ == "__main__":
    main()
