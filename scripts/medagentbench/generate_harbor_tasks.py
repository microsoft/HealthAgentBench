#!/usr/bin/env python3
"""Generate a single Harbor MedAgentBench meta-task from manifest-based tasks."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import inspect
import textwrap
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FIELDS = (
    "task_id",
    "instruction",
    "task_type",
    "category",
    "source_group",
    "source_benchmark",
)
DEFAULT_TASK_NAME = "medagentbench"
DEFAULT_SOURCE_BENCHMARK = "medagentbench"
ACTION_OVERRIDE_GROUPS = {"task3", "task5", "task8", "task9"}
DEFAULT_REFERENCE_TIME = "2023-11-13T10:15:00+00:00"
FHIR_IMAGE = "jyxsu6/medagentbench@sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966"
FHIR_READY_IMAGE = "curlimages/curl:8.12.1"


def _clean_block(value: str) -> str:
    return inspect.cleandoc(value) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-benchmark", default=DEFAULT_SOURCE_BENCHMARK)
    parser.add_argument(
        "--task-name",
        default=DEFAULT_TASK_NAME,
        help="Name of the generated Harbor task directory.",
    )
    parser.add_argument(
        "--selected-task-ids",
        help=(
            "Optional comma-separated task IDs to include in the benchmark slice. "
            "Defaults to one *_1 task from each MedAgentBench task group."
        ),
    )
    return parser.parse_args()


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_tasks(input_root: Path, source_benchmark: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    manifests = sorted(input_root.glob(f"*/sources/{source_benchmark}/*.yaml"))
    for manifest in manifests:
        payload = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        task_rows = payload.get("tasks", [])
        if not isinstance(task_rows, list):
            raise ValueError(f"Invalid tasks payload in {manifest}")

        for row in task_rows:
            if not isinstance(row, dict):
                raise ValueError(f"Invalid task row in {manifest}")
            task = dict(row)
            task["manifest_path"] = str(manifest)
            _validate_task(task)
            task_id = str(task["task_id"])
            if task_id in seen_ids:
                raise ValueError(f"Duplicate task_id detected: {task_id}")
            seen_ids.add(task_id)
            rows.append(task)

    return sorted(rows, key=lambda item: str(item["task_id"]))


def _validate_task(task: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not str(task.get(field, "")).strip()]
    if missing:
        task_id = task.get("task_id", "<missing-task-id>")
        raise ValueError(f"Task {task_id} missing required fields: {', '.join(missing)}")


def _default_selected_task_ids(tasks: list[dict[str, Any]]) -> list[str]:
    grouped: dict[str, set[str]] = {}
    for task in tasks:
        group = str(task.get("source_group", "")).strip()
        task_id = str(task.get("task_id", "")).strip()
        if not group or not task_id:
            continue
        grouped.setdefault(group, set()).add(task_id)

    selected: list[str] = []
    def _group_sort_key(value: str) -> tuple[int, str]:
        suffix = value.removeprefix("task")
        return (int(suffix) if suffix.isdigit() else 10**9, value)

    for group in sorted(grouped, key=_group_sort_key):
        preferred = f"{group}_1"
        if preferred not in grouped[group]:
            raise ValueError(
                f"Expected representative task {preferred} for group {group}, "
                f"but available task IDs are {sorted(grouped[group])[:5]}..."
            )
        selected.append(preferred)
    return selected


def _select_tasks(tasks: list[dict[str, Any]], selected_task_ids: list[str]) -> list[dict[str, Any]]:
    by_id = {str(task["task_id"]): task for task in tasks}
    missing = [task_id for task_id in selected_task_ids if task_id not in by_id]
    if missing:
        raise ValueError(f"Unknown selected task IDs: {', '.join(missing)}")
    return [dict(by_id[task_id]) for task_id in selected_task_ids]


def _evaluation_focus(task: dict[str, Any]) -> str:
    group = str(task.get("source_group", ""))
    return "tool_trace" if group in ACTION_OVERRIDE_GROUPS else "final_answer"


def _benchmark_tasks_payload(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    payload_tasks: list[dict[str, Any]] = []
    for task in tasks:
        payload_tasks.append(
            {
                "task_id": str(task["task_id"]),
                "category": task.get("category"),
                "difficulty": task.get("difficulty"),
                "instruction": task.get("instruction"),
                "task_type": task.get("task_type"),
                "source_group": task.get("source_group"),
                "source_task_type": task.get("source_task_type"),
                "expected_answer": task.get("expected_answer"),
                "required_actions": task.get("required_actions", []),
                "allowed_tools": task.get("allowed_tools", []),
                "eval_mrn": task.get("eval_mrn"),
                "manifest_path": task.get("manifest_path"),
                "evaluation_focus": _evaluation_focus(task),
            }
        )

    return {
        "benchmark_name": DEFAULT_SOURCE_BENCHMARK,
        "reference_time": DEFAULT_REFERENCE_TIME,
        "fhir_base_url": "http://fhir:8080/fhir",
        "submission_path": "/workspace/submission.json",
        "tasks": payload_tasks,
    }


def _action_payload_templates(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    templates: dict[str, Any] = {}
    for task in tasks:
        task_id = str(task["task_id"])
        eval_mrn = str(task.get("eval_mrn", ""))
        if task_id == "task3_1":
            templates[task_id] = {
                "tool_trace": [
                    {
                        "tool": "vital_create",
                        "status": "ok",
                        "args": {
                            "resource": {
                                "resourceType": "Observation",
                                "status": "final",
                                "category": [
                                    {
                                        "coding": [
                                            {
                                                "system": "http://hl7.org/fhir/observation-category",
                                                "code": "vital-signs",
                                                "display": "Vital Signs",
                                            }
                                        ]
                                    }
                                ],
                                "code": {"text": "BP"},
                                "effectiveDateTime": DEFAULT_REFERENCE_TIME,
                                "valueString": "118/77 mmHg",
                                "subject": {"reference": f"Patient/{eval_mrn}"},
                            }
                        },
                    }
                ]
            }
        elif task_id == "task5_1":
            templates[task_id] = {
                "tool_trace": [],
                "notes": "For this selected case, the expected action is no write because the recent magnesium value is unavailable.",
            }
        elif task_id == "task8_1":
            templates[task_id] = {
                "tool_trace": [
                    {
                        "tool": "procedure_create",
                        "status": "ok",
                        "args": {
                            "resource": {
                                "resourceType": "ServiceRequest",
                                "status": "active",
                                "intent": "order",
                                "authoredOn": DEFAULT_REFERENCE_TIME,
                                "priority": "stat",
                                "code": {
                                    "coding": [
                                        {
                                            "system": "http://snomed.info/sct",
                                            "code": "306181000000106",
                                        }
                                    ]
                                },
                                "note": [
                                    {
                                        "text": "Situation: acute left knee injury, Background: radiology report indicates ACL tear. Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to evaluate and provide management recommendations."
                                    }
                                ],
                                "subject": {"reference": f"Patient/{eval_mrn}"},
                            }
                        },
                    }
                ]
            }
        elif task_id == "task9_1":
            templates[task_id] = {
                "tool_trace": [],
                "notes": "For this selected case, the potassium level is already at goal, so the expected action is no write.",
            }
    return templates


def _submission_template(tasks: list[dict[str, Any]], action_templates: dict[str, Any]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task["task_id"])
        row: dict[str, Any] = {
            "task_id": task_id,
            "final_answer": "",
            "tool_trace": [],
            "notes": (
                "Fill final_answer for query-style scoring. For action-scored tasks, "
                "fill tool_trace and leave final_answer blank unless the task explicitly asks for one."
            ),
        }
        if task_id in action_templates:
            row["tool_trace"] = action_templates[task_id]["tool_trace"]
            row["notes"] = action_templates[task_id].get("notes", row["notes"])
        results.append(row)

    return {
        "submission_path": "/workspace/submission.json",
        "instructions": {
            "query_tasks": "Return only the requested answer in final_answer.",
            "action_tasks": (
                "Do not mutate the database for action tasks. Instead, record the intended "
                "FHIR write operation(s) in tool_trace using the exact tool names and a resource payload under args.resource."
            ),
        },
        "results": results,
    }


def _instruction_md(tasks: list[dict[str, Any]]) -> str:
    bullet_lines = []
    for task in tasks:
        bullet_lines.append(
            f"- `{task['task_id']}` ({task.get('category')}, {task.get('source_group')}): {task.get('instruction')}"
        )

    return "\n".join(
        [
            "# MedAgentBench Meta-Task",
            "",
            "You are working inside a Harbor task environment that contains:",
            "",
            "- a local FHIR server at `http://fhir:8080/fhir`",
            "- the selected MedAgentBench slice at `/workspace/benchmark_tasks.json`",
            "- helper scripts under `/workspace/scripts/`",
            "- a submission template at `/workspace/submission_template.json`",
            "",
            "Your job is to solve every benchmark item in `/workspace/benchmark_tasks.json` and write your final answers to `/workspace/submission.json`.",
            "",
            "Rules:",
            "",
            "- For query-scored tasks, fill `final_answer` only.",
            "- For action-scored tasks, do not mutate the database. Instead, write the intended FHIR action payload(s) in `tool_trace` using the exact tool names and the shape shown in `/workspace/submission_template.json`.",
            "- Keep the submission file as valid JSON.",
            "- You may use the helper scripts or inspect the raw FHIR API directly.",
            "",
            "Suggested workflow:",
            "",
            "1. Run `/workspace/scripts/wait_for_fhir.sh`.",
            "2. Copy `/workspace/submission_template.json` to `/workspace/submission.json`.",
            "3. Use `/workspace/scripts/fhir_tools.py` to query patients and observations.",
            "4. For action tasks, inspect `/workspace/action_payload_templates.json` or run `/workspace/scripts/show_action_template.py <task_id>`.",
            "5. Fill `/workspace/submission.json` and stop when all 10 tasks are complete.",
            "",
            "Selected tasks in this slice:",
            "",
            *bullet_lines,
            "",
        ]
    )


def _task_toml(selected_task_ids: list[str]) -> str:
    selection_json = json.dumps(selected_task_ids)
    return "\n".join(
        [
            'version = "1.0"',
            "",
            "[metadata]",
            'benchmark = "medagentbench"',
            'mode = "meta-task"',
            f"selected_task_ids = {selection_json}",
            'submission_path = "/workspace/submission.json"',
            "",
            "[verifier]",
            "timeout_sec = 900.0",
            "",
            "[agent]",
            "timeout_sec = 3600.0",
            "",
            "[environment]",
            "build_timeout_sec = 1800.0",
            "allow_internet = false",
            "cpus = 2",
            "memory_mb = 4096",
            "storage_mb = 10240",
            "gpus = 0",
            "mcp_servers = []",
            "",
            "[verifier.env]",
            "",
            "[solution.env]",
            "",
        ]
    )


def _workspace_readme() -> str:
    return textwrap.dedent(
        """
        # Workspace Files

        - `benchmark_tasks.json`: the 10 selected MedAgentBench items to solve.
        - `submission_template.json`: copy this to `submission.json` and fill it in.
        - `action_payload_templates.json`: example payload shapes for the action-scored tasks.
        - `scripts/fhir_tools.py`: helper CLI for common FHIR queries.
        - `scripts/show_action_template.py <task_id>`: print the template payload for an action task.
        - `scripts/wait_for_fhir.sh`: wait until the local FHIR endpoint is ready.

        The verifier reads `/workspace/submission.json` after the agent stops.
        """
    ).strip() + "\n"


def _environment_dockerfile() -> str:
    return textwrap.dedent(
        """
        FROM python:3.12-slim

        RUN apt-get update \
            && apt-get install -y --no-install-recommends bash curl jq \
            && rm -rf /var/lib/apt/lists/*

        WORKDIR /workspace
        COPY workspace/ /workspace/
        RUN chmod +x /workspace/scripts/*.sh
        """
    ).strip() + "\n"


def _environment_compose() -> str:
    return textwrap.dedent(
        f"""
        services:
          main:
            environment:
              FHIR_BASE_URL: http://fhir:8080/fhir
            depends_on:
              fhir-ready:
                condition: service_completed_successfully

          fhir:
            image: {FHIR_IMAGE}

          fhir-ready:
            image: {FHIR_READY_IMAGE}
            depends_on:
              - fhir
            command:
              - sh
              - -lc
              - |
                for _ in $(seq 1 120); do
                  if curl -fsS http://fhir:8080/fhir/metadata >/dev/null 2>&1; then
                    exit 0
                  fi
                  sleep 2
                done
                exit 1
        """
    ).strip() + "\n"


def _fhir_tools_py() -> str:
    return _clean_block(
        """
        #!/usr/bin/env python3
        # Small helper CLI for reading the local FHIR server.

        from __future__ import annotations

        import argparse
        import json
        import os
        import urllib.parse
        import urllib.request
        from datetime import datetime, timedelta
        from typing import Any


        def _base_url() -> str:
            return os.environ.get("FHIR_BASE_URL", "http://fhir:8080/fhir").rstrip("/")


        def _get_json(path: str) -> dict[str, Any]:
            url = f"{_base_url()}/{path.lstrip('/')}"
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))


        def _print(payload: Any) -> None:
            print(json.dumps(payload, indent=2, ensure_ascii=False))


        def _patient_search(name: str | None, birthdate: str | None, mrn: str | None) -> None:
            if mrn:
                query = f"Patient?identifier={urllib.parse.quote(mrn)}&_format=json"
            else:
                params = []
                if name:
                    params.append(f"name={urllib.parse.quote(name)}")
                if birthdate:
                    params.append(f"birthdate={urllib.parse.quote(birthdate)}")
                params.append("_format=json")
                query = "Patient?" + "&".join(params)
            _print(_get_json(query))


        def _observation_search(patient: str, code: str) -> None:
            query = (
                f"Observation?patient={urllib.parse.quote(patient)}"
                f"&code={urllib.parse.quote(code)}&_count=5000&_format=json"
            )
            _print(_get_json(query))


        def _parse_dt(value: str | None) -> datetime | None:
            if not value:
                return None
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None


        def _observations(patient: str, code: str) -> list[dict[str, Any]]:
            bundle = _get_json(
                f"Observation?patient={urllib.parse.quote(patient)}&code={urllib.parse.quote(code)}&_count=5000&_format=json"
            )
            return [entry.get("resource", {}) for entry in bundle.get("entry", []) if isinstance(entry, dict)]


        def _quantity_value(resource: dict[str, Any]) -> float | None:
            value = resource.get("valueQuantity", {}).get("value")
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None


        def _latest_observation(patient: str, code: str, within_hours: int | None) -> None:
            cutoff = None
            if within_hours is not None:
                cutoff = datetime.fromisoformat("2023-11-13T10:15:00+00:00") - timedelta(hours=within_hours)
            best = None
            best_dt = None
            for resource in _observations(patient, code):
                effective_dt = _parse_dt(resource.get("effectiveDateTime"))
                if effective_dt is None:
                    continue
                if cutoff is not None and effective_dt < cutoff:
                    continue
                if best_dt is None or effective_dt > best_dt:
                    best_dt = effective_dt
                    best = resource
            _print(best or {})


        def _average_observation(patient: str, code: str, within_hours: int) -> None:
            cutoff = datetime.fromisoformat("2023-11-13T10:15:00+00:00") - timedelta(hours=within_hours)
            values: list[float] = []
            for resource in _observations(patient, code):
                effective_dt = _parse_dt(resource.get("effectiveDateTime"))
                value = _quantity_value(resource)
                if effective_dt is None or value is None:
                    continue
                if effective_dt >= cutoff:
                    values.append(value)
            payload = {
                "count": len(values),
                "average": -1 if not values else sum(values) / len(values),
                "values": values,
            }
            _print(payload)


        def _patient_age(mrn: str, reference_time: str) -> None:
            bundle = _get_json(f"Patient?identifier={urllib.parse.quote(mrn)}&_format=json")
            entries = bundle.get("entry", [])
            if not entries:
                _print({"mrn": mrn, "age": -1, "error": "Patient not found"})
                return
            resource = entries[0].get("resource", {})
            birthdate = resource.get("birthDate")
            if not birthdate:
                _print({"mrn": mrn, "age": -1, "error": "birthDate missing"})
                return
            dob = datetime.strptime(birthdate, "%Y-%m-%d")
            now = datetime.fromisoformat(reference_time)
            age = now.year - dob.year
            if (now.month, now.day) < (dob.month, dob.day):
                age -= 1
            _print({"mrn": mrn, "birthDate": birthdate, "age": age})


        def main() -> None:
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest="command", required=True)

            patient_parser = subparsers.add_parser("patient-search")
            patient_parser.add_argument("--name")
            patient_parser.add_argument("--birthdate")
            patient_parser.add_argument("--mrn")

            observation_parser = subparsers.add_parser("observation-search")
            observation_parser.add_argument("--patient", required=True)
            observation_parser.add_argument("--code", required=True)

            latest_parser = subparsers.add_parser("latest-observation")
            latest_parser.add_argument("--patient", required=True)
            latest_parser.add_argument("--code", required=True)
            latest_parser.add_argument("--within-hours", type=int)

            average_parser = subparsers.add_parser("average-observation")
            average_parser.add_argument("--patient", required=True)
            average_parser.add_argument("--code", required=True)
            average_parser.add_argument("--within-hours", type=int, required=True)

            age_parser = subparsers.add_parser("patient-age")
            age_parser.add_argument("--mrn", required=True)
            age_parser.add_argument("--reference-time", default="2023-11-13T10:15:00+00:00")

            args = parser.parse_args()
            if args.command == "patient-search":
                _patient_search(args.name, args.birthdate, args.mrn)
            elif args.command == "observation-search":
                _observation_search(args.patient, args.code)
            elif args.command == "latest-observation":
                _latest_observation(args.patient, args.code, args.within_hours)
            elif args.command == "average-observation":
                _average_observation(args.patient, args.code, args.within_hours)
            elif args.command == "patient-age":
                _patient_age(args.mrn, args.reference_time)


        if __name__ == "__main__":
            main()
        """
    )


def _show_action_template_py() -> str:
    return _clean_block(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import json
        import sys
        from pathlib import Path


        def main() -> None:
            if len(sys.argv) != 2:
                raise SystemExit("usage: show_action_template.py <task_id>")
            task_id = sys.argv[1]
            templates_path = Path("/workspace/action_payload_templates.json")
            payload = json.loads(templates_path.read_text(encoding="utf-8"))
            if task_id not in payload:
                raise SystemExit(f"no action template for {task_id}")
            print(json.dumps(payload[task_id], indent=2, ensure_ascii=False))


        if __name__ == "__main__":
            main()
        """
    )


def _init_submission_py() -> str:
    return _clean_block(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import shutil
        from pathlib import Path


        def main() -> None:
            template = Path("/workspace/submission_template.json")
            target = Path("/workspace/submission.json")
            if target.exists():
                print(f"already exists: {target}")
                return
            shutil.copyfile(template, target)
            print(f"created {target}")


        if __name__ == "__main__":
            main()
        """
    )


def _wait_for_fhir_sh() -> str:
    return _clean_block(
        """
        #!/usr/bin/env bash
        set -euo pipefail

        base_url="${FHIR_BASE_URL:-http://fhir:8080/fhir}"
        for _ in $(seq 1 60); do
          if curl -fsS "${base_url}/metadata" >/dev/null 2>&1; then
            echo "FHIR is ready at ${base_url}"
            exit 0
          fi
          sleep 2
        done
        echo "FHIR was not ready in time: ${base_url}" >&2
        exit 1
        """
    )


def _test_sh() -> str:
    return _clean_block(
        """
        #!/usr/bin/env bash
        set -euo pipefail

        mkdir -p /logs/verifier
        python /tests/verify_meta_task.py \
          --submission /workspace/submission.json \
          --tasks /workspace/benchmark_tasks.json \
          --reward-file /logs/verifier/reward.txt
        """
    )


def _verify_meta_task_py() -> str:
    return _clean_block(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path
        from typing import Any

        from evaluator import evaluate_results


        def _load_json(path: Path) -> Any:
            return json.loads(path.read_text(encoding="utf-8"))


        def _normalize_tool_trace(value: Any) -> list[dict[str, Any]]:
            if not isinstance(value, list):
                return []
            normalized: list[dict[str, Any]] = []
            for entry in value:
                if not isinstance(entry, dict):
                    continue
                if "args" in entry and isinstance(entry.get("args"), dict):
                    normalized.append(entry)
                    continue
                tool = entry.get("tool")
                resource = entry.get("resource")
                if isinstance(tool, str) and isinstance(resource, dict):
                    normalized.append(
                        {
                            "tool": tool,
                            "status": entry.get("status", "ok"),
                            "args": {"resource": resource},
                        }
                    )
            return normalized


        def _build_results(tasks_payload: dict[str, Any], submission_payload: dict[str, Any]) -> list[dict[str, Any]]:
            tasks = tasks_payload.get("tasks", [])
            submitted_rows = submission_payload.get("results", [])
            submitted_by_id = {
                str(row.get("task_id")): row
                for row in submitted_rows
                if isinstance(row, dict) and row.get("task_id")
            }

            rows: list[dict[str, Any]] = []
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                task_id = str(task.get("task_id", ""))
                submitted = submitted_by_id.get(task_id, {})
                row = dict(task)
                row["final_answer"] = submitted.get("final_answer", "")
                row["tool_trace"] = _normalize_tool_trace(submitted.get("tool_trace", []))
                if task_id not in submitted_by_id:
                    row["error_type"] = "missing_submission"
                rows.append(row)
            return rows


        def main() -> None:
            parser = argparse.ArgumentParser()
            parser.add_argument("--submission", type=Path, required=True)
            parser.add_argument("--tasks", type=Path, required=True)
            parser.add_argument("--reward-file", type=Path, required=True)
            args = parser.parse_args()

            if not args.submission.exists():
                args.reward_file.write_text("0\\n", encoding="utf-8")
                print(f"missing submission file: {args.submission}")
                return

            tasks_payload = _load_json(args.tasks)
            submission_payload = _load_json(args.submission)
            rows = _build_results(tasks_payload, submission_payload)

            results_path = args.reward_file.parent / "meta_results.jsonl"
            with results_path.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\\n")

            summary = evaluate_results(str(results_path))
            args.reward_file.write_text(f"{summary['pass_at_1']:.6f}\\n", encoding="utf-8")
            print(json.dumps(summary, indent=2, ensure_ascii=False))


        if __name__ == "__main__":
            main()
        """
    )


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_meta_task(
    *,
    selected_tasks: list[dict[str, Any]],
    selected_task_ids: list[str],
    output_root: Path,
    task_name: str,
) -> None:
    tasks_parent = output_root.parent
    if output_root.exists():
        shutil.rmtree(output_root)
    tasks_parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "harbor",
            "tasks",
            "init",
            task_name,
            "--tasks-dir",
            str(tasks_parent),
            "--no-pytest",
            "--no-solution",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    task_dir = output_root
    benchmark_payload = _benchmark_tasks_payload(selected_tasks)
    action_templates = _action_payload_templates(selected_tasks)
    submission_template = _submission_template(selected_tasks, action_templates)

    task_dir.joinpath("instruction.md").write_text(
        _instruction_md(selected_tasks), encoding="utf-8"
    )
    task_dir.joinpath("task.toml").write_text(
        _task_toml(selected_task_ids), encoding="utf-8"
    )
    _write_json(task_dir / "benchmark_tasks.json", benchmark_payload)
    _write_json(task_dir / "action_payload_templates.json", action_templates)
    _write_json(task_dir / "submission_template.json", submission_template)

    environment_dir = task_dir / "environment"
    workspace_dir = environment_dir / "workspace"
    scripts_dir = workspace_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    environment_dir.joinpath("Dockerfile").write_text(
        _environment_dockerfile(), encoding="utf-8"
    )
    environment_dir.joinpath("docker-compose.yaml").write_text(
        _environment_compose(), encoding="utf-8"
    )
    workspace_dir.joinpath("README.md").write_text(_workspace_readme(), encoding="utf-8")
    _write_json(workspace_dir / "benchmark_tasks.json", benchmark_payload)
    _write_json(workspace_dir / "action_payload_templates.json", action_templates)
    _write_json(workspace_dir / "submission_template.json", submission_template)
    submission_path = workspace_dir / "submission.json"
    if submission_path.exists():
        submission_path.unlink()
    scripts_dir.joinpath("fhir_tools.py").write_text(_fhir_tools_py(), encoding="utf-8")
    scripts_dir.joinpath("show_action_template.py").write_text(
        _show_action_template_py(), encoding="utf-8"
    )
    scripts_dir.joinpath("init_submission.py").write_text(
        _init_submission_py(), encoding="utf-8"
    )
    wait_path = scripts_dir / "wait_for_fhir.sh"
    wait_path.write_text(_wait_for_fhir_sh(), encoding="utf-8")
    wait_path.chmod(0o755)
    for script_name in ("fhir_tools.py", "show_action_template.py", "init_submission.py"):
        (scripts_dir / script_name).chmod(0o755)

    tests_dir = task_dir / "tests"
    test_sh = tests_dir / "test.sh"
    test_sh.write_text(_test_sh(), encoding="utf-8")
    test_sh.chmod(0o755)
    tests_dir.joinpath("verify_meta_task.py").write_text(
        _verify_meta_task_py(), encoding="utf-8"
    )
    evaluator_src = Path("scripts/medagentbench/evaluator.py")
    tests_dir.joinpath("evaluator.py").write_text(
        evaluator_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    pycache_dir = tests_dir / "__pycache__"
    if pycache_dir.exists():
        shutil.rmtree(pycache_dir)



def main() -> None:
    args = _parse_args()
    tasks = _load_tasks(args.input_root, args.source_benchmark)
    selected_task_ids = _split_csv(args.selected_task_ids) or _default_selected_task_ids(tasks)
    selected_tasks = _select_tasks(tasks, selected_task_ids)

    _write_meta_task(
        selected_tasks=selected_tasks,
        selected_task_ids=selected_task_ids,
        output_root=args.output_root,
        task_name=args.task_name,
    )

    summary = {
        "output_root": str(args.output_root),
        "task_name": args.task_name,
        "task_count": len(selected_tasks),
        "selected_task_ids": selected_task_ids,
        "source_benchmark": args.source_benchmark,
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
