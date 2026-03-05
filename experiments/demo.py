#!/usr/bin/env python3
"""Interactive terminal demo for ad-hoc MedAgentBench-style prompts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

from ehr_co_scientist.agent import AgentConfig, run_task
from ehr_co_scientist.backends.adapter import BackendConfig
from ehr_co_scientist.tools.catalog import TOOL_DEFINITIONS
from ehr_co_scientist.tools.tooling.function_tools import get_openai_function_tools


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive EHR Co-Scientist demo")
    parser.add_argument("--backend", default="azure_openai")
    parser.add_argument("--model", default="gpt-5.2")
    parser.add_argument("--api-version", default="2025-03-01-preview")
    parser.add_argument("--fhir-base-url", default="http://localhost:8080/fhir")
    parser.add_argument("--endpoint-name", default=None)
    parser.add_argument("--max-rounds", type=int, default=8)
    parser.add_argument(
        "--evaluation-mode",
        action="store_true",
        help=(
            "Do not execute write tools in evaluation mode; terminate task early "
            "when a write tool is called."
        ),
    )
    parser.add_argument(
        "--disable-default-tools",
        action="store_true",
        help="Disable default FHIR function-calling tools in demo requests.",
    )
    parser.add_argument(
        "--show-full-trace",
        action="store_true",
        help=(
            "Include full execution trace in output "
            "(tool trace details and backend response payload)."
        ),
    )
    return parser


def _result_payload(
    task_id: str,
    prompt: str,
    result: dict[str, Any],
    *,
    show_full_trace: bool,
) -> dict[str, Any]:
    tool_trace = result.get("tool_trace", [])
    payload = {
        "task_id": task_id,
        "prompt": prompt,
        "final_answer": result.get("final_answer", ""),
        "rounds_used": result.get("rounds_used", 0),
        "error": result.get("error"),
        "terminated_early": result.get("terminated_early", False),
        "termination_reason": result.get("termination_reason"),
        "tool_trace_count": len(tool_trace),
        "tool_trace_summary": [
            {
                "tool": entry.get("tool"),
                "status": entry.get("status"),
            }
            for entry in tool_trace
        ],
    }
    if show_full_trace:
        payload["tool_trace"] = tool_trace
        payload["backend_result"] = result.get("backend_result")
    return payload


def main() -> None:
    args = _build_parser().parse_args()

    backend_config = BackendConfig(
        backend=args.backend,
        model=args.model,
        endpoint_name=args.endpoint_name,
        api_version=args.api_version,
    )
    agent_config = AgentConfig(
        max_rounds=args.max_rounds,
        evaluation_mode=args.evaluation_mode,
    )
    chat_kwargs: dict[str, Any] = {}
    if not args.disable_default_tools:
        chat_kwargs["tools"] = get_openai_function_tools(TOOL_DEFINITIONS)
        chat_kwargs["tool_choice"] = "auto"
        chat_kwargs["parallel_tool_calls"] = False

    print("EHR Co-Scientist Demo")
    print("Type a prompt and press Enter. Type 'quit' or 'exit' to stop.")

    counter = 0
    while True:
        try:
            prompt = input("demo> ").strip()
        except EOFError:
            print("\nExiting demo.")
            break

        if not prompt:
            continue
        if prompt.lower() in {"quit", "exit"}:
            print("Exiting demo.")
            break

        counter += 1
        task_id = f"demo_{counter}"
        task = {
            "task_id": task_id,
            "instruction": prompt,
            "category": "interactive_demo",
            "task_type": "query",
            "difficulty": "unknown",
        }

        started = datetime.now(timezone.utc)
        try:
            result = run_task(
                task=task,
                backend_config=backend_config,
                fhir_base_url=args.fhir_base_url,
                config=agent_config,
                chat_kwargs=chat_kwargs,
            )
            payload = _result_payload(
                task_id,
                prompt,
                result,
                show_full_trace=args.show_full_trace,
            )
            payload["generated_at"] = started.isoformat()
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        except Exception as exc:  # noqa: BLE001
            print(
                json.dumps(
                    {
                        "task_id": task_id,
                        "prompt": prompt,
                        "error": str(exc),
                        "generated_at": started.isoformat(),
                    },
                    indent=2,
                    ensure_ascii=True,
                )
            )


if __name__ == "__main__":
    main()
