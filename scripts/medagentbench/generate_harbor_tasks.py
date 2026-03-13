#!/usr/bin/env python3
"""Generate a single Harbor MedAgentBench meta-task from raw benchmark JSON."""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any

from scripts.medagentbench.normalization import (
    build_harbor_answer_key,
    default_selected_task_ids,
    infer_group,
    load_raw_tasks,
    normalize_harbor_task,
)


DEFAULT_TASK_NAME = "medagentbench"
DEFAULT_INPUT_JSON = Path("data/medagentbench/test_data_v2.json")
DEFAULT_REFERENCE_TIME = "2023-11-13T10:15:00+00:00"
FHIR_IMAGE = "jyxsu6/medagentbench@sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966"
FHIR_READY_IMAGE = "curlimages/curl:8.12.1"


def _clean_block(value: str) -> str:
    return inspect.cleandoc(value) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-json",
        type=Path,
        default=DEFAULT_INPUT_JSON,
        help="Raw MedAgentBench task JSON file.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
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


def _select_tasks(raw_tasks: list[dict[str, Any]], selected_task_ids: list[str]) -> list[dict[str, Any]]:
    by_id = {str(task["id"]): task for task in raw_tasks if task.get("id")}
    missing = [task_id for task_id in selected_task_ids if task_id not in by_id]
    if missing:
        raise ValueError(f"Unknown selected task IDs: {', '.join(missing)}")
    return [dict(by_id[task_id]) for task_id in selected_task_ids]


def _benchmark_tasks_payload(raw_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "reference_time": DEFAULT_REFERENCE_TIME,
        "submission_path": "/workspace/submission.json",
        "tasks": [normalize_harbor_task(task) for task in raw_tasks],
    }


def _expected_payload(task_id: str, eval_mrn: str) -> Any:
    if task_id == "task3_1":
        return {
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
    if task_id == "task8_1":
        return {
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
            "note": {
                "text": (
                    "Situation: acute left knee injury, Background: radiology report indicates ACL tear. "
                    "Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to "
                    "evaluate and provide management recommendations."
                )
            },
            "subject": {"reference": f"Patient/{eval_mrn}"},
        }
    if task_id == "task10_1":
        return {
            "resourceType": "ServiceRequest",
            "status": "active",
            "intent": "order",
            "authoredOn": DEFAULT_REFERENCE_TIME,
            "priority": "stat",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "4548-4",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{eval_mrn}"},
        }
    return None


def _action_payload_templates(raw_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    templates: dict[str, Any] = {}
    for task in raw_tasks:
        task_id = str(task["id"])
        templates[task_id] = _expected_payload(task_id, str(task.get("eval_MRN", "")))
    return templates


def _answer_key_payload(raw_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [build_harbor_answer_key(task) for task in raw_tasks]


def _submission_template(raw_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in raw_tasks:
        row = {
            "task_id": str(task.get("id", task.get("task_id", ""))),
            "instruction": str(task.get("instruction", "")),
            "context": str(task.get("context", "")),
            "final_answer": "",
            "payload": None,
        }
        rows.append(row)
    return rows


def _instruction_md(tasks_payload: dict[str, Any]) -> str:
    bullet_lines = []
    for task in tasks_payload["tasks"]:
        bullet_lines.append(
            f"- `{task['task_id']}` ({task['category']}, {task['difficulty']}): {task['instruction']}"
        )
    return "\n".join(
        [
            "# MedAgentBench Meta-Task",
            "",
            "You are working inside a Harbor task environment that contains:",
            "",
            "- a local FHIR server at `http://fhir:8080/fhir`",
            "- the selected MedAgentBench task slice at `/workspace/benchmark_tasks.json`",
            "- the selected tasks plus editable result fields in `/workspace/submission_template.json`",
            "- primitive FHIR helper scripts under `/workspace/scripts/`",
            "",
            "Original MedAgentBench expects one action at a time using `GET ...`, `POST ...`, or `FINISH(...)` with no extra text.",
            "This Harbor adaptation keeps the primitive MedAgentBench task semantics, but your final work product is `/workspace/submission.json`.",
            "",
            "Submission rules:",
            "",
            "- `/workspace/submission.json` is a JSON list. Each row contains `task_id`, task text, and exactly two editable result fields: `final_answer` and `payload`.",
            "- For query-only tasks, set `final_answer` and leave `payload` as `null`.",
            "- For write tasks, use the simulated POST helpers. They do not mutate the database; instead they print an accepted payload for you to copy into `payload`.",
            "- If a task needs multiple writes, set `payload` to a list of payload objects in call order. Otherwise use one payload object or `null`.",
            "- Do not add new fields to the submission rows.",
            "",
            "Suggested workflow:",
            "",
            "1. Run `/workspace/scripts/wait_for_fhir.sh`.",
            "2. Copy `/workspace/submission_template.json` to `/workspace/submission.json`.",
            "3. Use `/workspace/scripts/fhir_primitives.py` GET commands to inspect the chart.",
            "4. For write tasks, use the simulated POST commands and copy the returned payload into the row's `payload` field.",
            "5. Update `final_answer` where the task expects one, then stop when every selected row is complete.",
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

        - `benchmark_tasks.json`: normalized MedAgentBench task rows used for task browsing.
        - `submission_template.json`: copy this to `submission.json` and fill in `final_answer` and `payload`.
        - `scripts/fhir_primitives.py`: primitive GET and simulated POST helpers.
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
        """
    ).strip() + "\n"


def _environment_compose() -> str:
    return _clean_block(
        f"""
        services:
          main:
            environment:
              FHIR_BASE_URL: "http://fhir:8080/fhir"
            depends_on:
              fhir-ready:
                condition: service_completed_successfully
          fhir:
            image: {FHIR_IMAGE}
          fhir-ready:
            image: {FHIR_READY_IMAGE}
            depends_on:
              fhir:
                condition: service_started
            command:
              - sh
              - -c
              - >
                until curl -fsS http://fhir:8080/fhir/metadata >/dev/null; do
                  sleep 1;
                done
        """
    )


def _fhir_primitives_py() -> str:
    return _clean_block(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        import os
        import urllib.parse
        import urllib.request
        from pathlib import Path
        from typing import Any


        def _base_url() -> str:
            return os.environ.get("FHIR_BASE_URL", "http://fhir:8080/fhir").rstrip("/")


        def _print(payload: Any) -> None:
            print(json.dumps(payload, indent=2, ensure_ascii=False))


        def _get_json(path: str) -> dict[str, Any]:
            url = f"{_base_url()}/{path.lstrip('/')}"
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))


        def _query_string(params: dict[str, str | None]) -> str:
            pairs = [f"{key}={urllib.parse.quote(value)}" for key, value in params.items() if value]
            pairs.append("_format=json")
            return "&".join(pairs)


        def _get(resource: str, params: dict[str, str | None]) -> None:
            _print(_get_json(f"{resource}?{_query_string(params)}"))


        def _load_payload(path: str) -> dict[str, Any]:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise SystemExit("payload file must contain one JSON object")
            return payload


        def _simulate_post(resource_type: str, payload_file: str) -> None:
            payload = _load_payload(payload_file)
            if payload.get("resourceType") != resource_type:
                raise SystemExit(
                    f"payload resourceType mismatch: expected {resource_type}, got {payload.get('resourceType')}"
                )
            _print(
                {
                    "status": "accepted_simulated",
                    "resource_url": f"{_base_url()}/{resource_type}",
                    "payload": payload,
                    "message": "POST request accepted (simulated). Copy this payload into the task row's payload field and finish with the final answer.",
                }
            )


        def main() -> None:
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest="command", required=True)

            patient_parser = subparsers.add_parser("get-patient")
            for name in (
                "address",
                "address-city",
                "address-postalcode",
                "address-state",
                "birthdate",
                "family",
                "gender",
                "given",
                "identifier",
                "legal-sex",
                "name",
                "telecom",
            ):
                patient_parser.add_argument(f"--{name}")

            condition_parser = subparsers.add_parser("get-condition")
            condition_parser.add_argument("--patient", required=True)
            condition_parser.add_argument("--category")

            labs_parser = subparsers.add_parser("get-observation-labs")
            labs_parser.add_argument("--patient", required=True)
            labs_parser.add_argument("--code", required=True)
            labs_parser.add_argument("--date")

            vitals_parser = subparsers.add_parser("get-observation-vitals")
            vitals_parser.add_argument("--patient", required=True)
            vitals_parser.add_argument("--category", required=True)
            vitals_parser.add_argument("--date")

            meds_parser = subparsers.add_parser("get-medicationrequest")
            meds_parser.add_argument("--patient", required=True)
            meds_parser.add_argument("--category")
            meds_parser.add_argument("--date")

            procedure_parser = subparsers.add_parser("get-procedure")
            procedure_parser.add_argument("--patient", required=True)
            procedure_parser.add_argument("--date", required=True)
            procedure_parser.add_argument("--code")

            obs_post = subparsers.add_parser("post-observation-vitals")
            obs_post.add_argument("--payload-file", required=True)

            med_post = subparsers.add_parser("post-medicationrequest")
            med_post.add_argument("--payload-file", required=True)

            svc_post = subparsers.add_parser("post-servicerequest")
            svc_post.add_argument("--payload-file", required=True)

            args = parser.parse_args()

            if args.command == "get-patient":
                _get(
                    "Patient",
                    {name: getattr(args, name.replace("-", "_")) for name in (
                        "address",
                        "address-city",
                        "address-postalcode",
                        "address-state",
                        "birthdate",
                        "family",
                        "gender",
                        "given",
                        "identifier",
                        "legal-sex",
                        "name",
                        "telecom",
                    )},
                )
            elif args.command == "get-condition":
                _get("Condition", {"patient": args.patient, "category": args.category})
            elif args.command == "get-observation-labs":
                _get("Observation", {"patient": args.patient, "code": args.code, "date": args.date})
            elif args.command == "get-observation-vitals":
                _get("Observation", {"patient": args.patient, "category": args.category, "date": args.date})
            elif args.command == "get-medicationrequest":
                _get("MedicationRequest", {"patient": args.patient, "category": args.category, "date": args.date})
            elif args.command == "get-procedure":
                _get("Procedure", {"patient": args.patient, "date": args.date, "code": args.code})
            elif args.command == "post-observation-vitals":
                _simulate_post("Observation", args.payload_file)
            elif args.command == "post-medicationrequest":
                _simulate_post("MedicationRequest", args.payload_file)
            elif args.command == "post-servicerequest":
                _simulate_post("ServiceRequest", args.payload_file)


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
        until curl -fsS "${base_url}/metadata" >/dev/null; do
          sleep 1
        done
        echo "FHIR ready: ${base_url}"
        """
    )


def _test_sh() -> str:
    return _clean_block(
        """
        #!/usr/bin/env bash
        set -euo pipefail

        python /tests/verify_meta_task.py \
          --submission /workspace/submission.json \
          --tasks /workspace/benchmark_tasks.json \
          --answer-key /tests/task_answer_key.json \
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

        from evaluator import evaluate_submission_rows, merge_submission_with_answer_key


        def _load_json(path: Path):
            return json.loads(path.read_text(encoding="utf-8"))


        def _normalize_submission(payload):
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict) and isinstance(payload.get("results"), list):
                return payload["results"]
            raise ValueError("submission.json must be a list or an object with a 'results' list")


        def main() -> None:
            parser = argparse.ArgumentParser()
            parser.add_argument("--submission", type=Path, required=True)
            parser.add_argument("--tasks", type=Path, required=True)
            parser.add_argument("--answer-key", type=Path, required=True)
            parser.add_argument("--reward-file", type=Path, required=True)
            args = parser.parse_args()

            if not args.submission.exists():
                args.reward_file.write_text("0\\n", encoding="utf-8")
                print(f"missing submission file: {args.submission}")
                return

            task_payload = _load_json(args.tasks)
            expected_ids = [row["task_id"] for row in task_payload.get("tasks", []) if isinstance(row, dict)]
            submission_rows = _normalize_submission(_load_json(args.submission))
            answer_key_rows = _load_json(args.answer_key)
            submitted_by_id = {
                str(row.get("task_id", row.get("id", ""))): row
                for row in submission_rows
                if isinstance(row, dict)
            }
            answers_by_id = {
                str(row.get("task_id", row.get("id", ""))): row
                for row in answer_key_rows
                if isinstance(row, dict)
            }

            rows = []
            for task_id in expected_ids:
                row = submitted_by_id.get(task_id)
                if row is None:
                    row = {"task_id": task_id, "final_answer": "", "payload": None}
                merged = merge_submission_with_answer_key(
                    [row], [answers_by_id.get(task_id, {"task_id": task_id})]
                )
                rows.extend(merged)

            summary = evaluate_submission_rows(rows)
            results_path = args.reward_file.parent / "meta_results.json"
            results_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
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
    selected_raw_tasks: list[dict[str, Any]],
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
    benchmark_payload = _benchmark_tasks_payload(selected_raw_tasks)
    action_templates = _action_payload_templates(selected_raw_tasks)
    answer_key = _answer_key_payload(selected_raw_tasks)
    submission_template = _submission_template(selected_raw_tasks)

    task_dir.joinpath("instruction.md").write_text(
        _instruction_md(benchmark_payload), encoding="utf-8"
    )
    task_dir.joinpath("task.toml").write_text(
        _task_toml(selected_task_ids), encoding="utf-8"
    )
    _write_json(task_dir / "benchmark_tasks.json", benchmark_payload)
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
    _write_json(workspace_dir / "submission_template.json", submission_template)
    submission_path = workspace_dir / "submission.json"
    if submission_path.exists():
        submission_path.unlink()
    scripts_dir.joinpath("fhir_primitives.py").write_text(
        _fhir_primitives_py(), encoding="utf-8"
    )
    scripts_dir.joinpath("init_submission.py").write_text(
        _init_submission_py(), encoding="utf-8"
    )
    wait_path = scripts_dir / "wait_for_fhir.sh"
    wait_path.write_text(_wait_for_fhir_sh(), encoding="utf-8")
    wait_path.chmod(0o755)
    for script_name in ("fhir_primitives.py", "init_submission.py"):
        (scripts_dir / script_name).chmod(0o755)

    tests_dir = task_dir / "tests"
    test_sh = tests_dir / "test.sh"
    test_sh.write_text(_test_sh(), encoding="utf-8")
    test_sh.chmod(0o755)
    tests_dir.joinpath("verify_meta_task.py").write_text(
        _verify_meta_task_py(), encoding="utf-8"
    )
    evaluator_src = Path("scripts/medagentbench/harbor_evaluator.py")
    tests_dir.joinpath("evaluator.py").write_text(
        evaluator_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    _write_json(tests_dir / "task_answer_key.json", answer_key)
    _write_json(tests_dir / "action_payload_templates.json", action_templates)


def main() -> None:
    args = _parse_args()
    raw_tasks = load_raw_tasks(args.input_json)
    selected_task_ids = _split_csv(args.selected_task_ids) or default_selected_task_ids(raw_tasks)
    selected_raw_tasks = _select_tasks(raw_tasks, selected_task_ids)

    _write_meta_task(
        selected_raw_tasks=selected_raw_tasks,
        selected_task_ids=selected_task_ids,
        output_root=args.output_root,
        task_name=args.task_name,
    )

    summary = {
        "input_json": str(args.input_json),
        "output_root": str(args.output_root),
        "task_name": args.task_name,
        "task_count": len(selected_raw_tasks),
        "selected_task_ids": selected_task_ids,
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
