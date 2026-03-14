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
    build_instruction,
    default_selected_task_ids,
    infer_group,
    load_raw_tasks,
    normalize_harbor_task,
)


DEFAULT_TASK_NAME = "medagentbench"
DEFAULT_INPUT_JSON = Path("data/medagentbench/test_data_v2.json")
DEFAULT_FUNCS_JSON = Path("data/medagentbench/funcs_v1.json")
DEFAULT_REFERENCE_TIME = "2023-11-13T10:15:00+00:00"
FHIR_IMAGE = "jyxsu6/medagentbench@sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966"
FHIR_READY_IMAGE = "curlimages/curl:8.12.1"

PRIMITIVE_TO_FUNC_NAME = {
    "get_condition": "GET {api_base}/Condition",
    "get_observation_labs": "GET {api_base}/Observation|labs",
    "get_observation_vitals": "GET {api_base}/Observation|vitals",
    "post_observation_vitals": "POST {api_base}/Observation",
    "get_medicationrequest": "GET {api_base}/MedicationRequest",
    "post_medicationrequest": "POST {api_base}/MedicationRequest",
    "get_procedure": "GET {api_base}/Procedure",
    "post_servicerequest": "POST {api_base}/ServiceRequest",
    "get_patient": "GET {api_base}/Patient",
}


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
    parser.add_argument(
        "--funcs-json",
        type=Path,
        default=DEFAULT_FUNCS_JSON,
        help="Original MedAgentBench primitive schema JSON file.",
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


def _load_funcs(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("funcs JSON must be a list")
    return [dict(entry) for entry in payload if isinstance(entry, dict)]


def _primitive_schemas(funcs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    schema_map: dict[str, dict[str, Any]] = {}
    for entry in funcs:
        name = str(entry.get("name", ""))
        if name == "GET {api_base}/Observation":
            description = str(entry.get("description", ""))
            key = "GET {api_base}/Observation|vitals" if "Vitals" in description else "GET {api_base}/Observation|labs"
        else:
            key = name
        schema_map[key] = {
            "primitive": next(
                (primitive for primitive, func_name in PRIMITIVE_TO_FUNC_NAME.items() if func_name == key),
                "",
            ),
            "name": name,
            "description": str(entry.get("description", "")),
            "parameters": entry.get("parameters", {}),
        }
    missing = [primitive for primitive, key in PRIMITIVE_TO_FUNC_NAME.items() if key not in schema_map]
    if missing:
        raise ValueError(f"Missing primitive schemas for: {', '.join(missing)}")
    return {primitive: schema_map[key] for primitive, key in PRIMITIVE_TO_FUNC_NAME.items()}


def _benchmark_tasks_payload(raw_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return [normalize_harbor_task(task) for task in raw_tasks]


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


def _answer_key_payload(raw_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in raw_tasks:
        task_id = str(task.get("id", task.get("task_id", "")))
        answer_row = build_harbor_answer_key(task)
        answer_row["payload"] = _expected_payload(task_id, str(task.get("eval_MRN", "")))
        rows.append(answer_row)
    return rows


def _submission_template(raw_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in raw_tasks:
        task_id = str(task.get("id", task.get("task_id", "")))
        row = {
            "task_id": task_id,
            "instruction": build_instruction(
                base_instruction=str(task.get("instruction", "")),
                context=str(task.get("context", "")),
                source_group=infer_group(task_id),
            ),
            "final_answer": "",
            "payload": None,
        }
        rows.append(row)
    return rows


def _instruction_md(tasks_payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# EHR Workflow Benchmark",
            "",
            "You are working inside a task environment that contains:",
            "",
            "- a local FHIR server at `http://fhir:8080/fhir`",
            "- task descriptions at `/workspace/benchmark_tasks.json`",
            "- editable task rows already prepared at `/workspace/submission.json`",
            "- primitive FHIR helper scripts under `/workspace/scripts/primitives/` (each supports `--help`)",
            "",
            "Primitive helper examples:",
            "- `python /workspace/scripts/primitives/get_patient.py --help`",
            "- `python /workspace/scripts/primitives/get_patient.py --identifier S2874099`",
            "- `python /workspace/scripts/primitives/get_observation_labs.py --patient S2823623 --code GLU`",
            "- `python /workspace/scripts/primitives/post_servicerequest.py --help`",
            "",
            "This benchmark simulates realistic EHR workflows in which each task may require multiple retrieval and action steps over patient data.",
            "The environment provides API-style helper scripts for interacting with the EHR. Work through the tasks carefully and complete each row accurately.",
            "",
            "Your final work product is `/workspace/submission.json`.",
            "",
            "Suggested workflow:",
            "",
            "1. Choose one row from `/workspace/submission.json`.",
            "2. Read that row's instruction carefully.",
            "3. Use the helper scripts under `/workspace/scripts/primitives/` when you need to query the chart or simulate a write. Start with `--help` if you are unsure which primitive to use. For write primitives, `--help` also shows the expected payload schema.",
            "4. Write the row's `final_answer` and `payload`, then move to the next row.",
            "5. Stop when every row is complete.",
            "",
            "Submission rules:",
            "",
            "- `/workspace/submission.json` is a JSON list. Each row contains `task_id`, task text, and exactly two editable result fields: `final_answer` and `payload`.",
            "- For query-only tasks, set `final_answer` and leave `payload` as `null`.",
            "- For write tasks, use the simulated POST helpers. They do not mutate the database; instead they print an accepted payload for you to copy into `payload`.",
            "- If a task needs multiple writes, set `payload` to a list of payload objects in call order. Otherwise use one payload object or `null`.",
            "- Do not add new fields to the submission rows.",
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

        - `benchmark_tasks.json`: normalized task rows used for task browsing.
        - `submission.json`: editable task rows; fill in `final_answer` and `payload`.
        - `scripts/primitives/get_*.py`: primitive read helpers; each supports `--help`.
        - `scripts/primitives/post_*.py`: simulated write helpers; each supports `--help`.
        - `scripts/lib/fhir_common.py`: shared HTTP and payload helpers used by the primitive scripts.

        Primitive helper examples:

        - `python /workspace/scripts/primitives/get_patient.py --help`
        - `python /workspace/scripts/primitives/get_patient.py --identifier S2874099`
        - `python /workspace/scripts/primitives/get_observation_labs.py --patient S2823623 --code GLU`
        - `python /workspace/scripts/primitives/post_servicerequest.py --help`

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


def _fhir_common_py() -> str:
    return _clean_block(
        """
        from __future__ import annotations

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
        """
    )


def _primitive_script_py(
    *,
    description: str,
    schema: dict[str, Any],
    arg_lines: list[str],
    body_lines: list[str],
    include_schema_in_help: bool = False,
) -> str:
    required = schema.get("parameters", {}).get("required", [])
    epilog_lines: list[str] = []
    if include_schema_in_help:
        epilog_lines.append("Original payload schema:")
        epilog_lines.append(json.dumps(schema.get("parameters", {}), indent=2, ensure_ascii=False))
    elif required:
        epilog_lines.append(f"Required flags: {', '.join(f'--{name}' for name in required)}")
    epilog = "\n\n".join(epilog_lines) if epilog_lines else None
    return _clean_block(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "",
                "import argparse",
                "import sys",
                "from pathlib import Path",
                "",
                'sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))',
                "from fhir_common import _get, _simulate_post",
                "",
                "def main() -> None:",
                f"    parser = argparse.ArgumentParser(",
                f"        description={description!r},",
                "        formatter_class=argparse.RawTextHelpFormatter,",
                f"        epilog={epilog!r},",
                "    )",
                *[f"    {line}" for line in arg_lines],
                "    args = parser.parse_args()",
                *[f"    {line}" for line in body_lines],
                "",
                "",
                'if __name__ == "__main__":',
                "    main()",
            ]
        )
    )


def _primitive_scripts(schemas: dict[str, dict[str, Any]]) -> dict[str, str]:
    patient_fields = [
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
    ]
    patient_args = [
        f'parser.add_argument("--{name}", help="FHIR Patient search parameter: {name}")'
        for name in patient_fields
    ]
    patient_body = [
        '_get("Patient", {'
        + ", ".join(
            [f'"{name}": args.{name.replace("-", "_")}' for name in patient_fields]
        )
        + '})'
    ]
    return {
        "get_patient.py": _primitive_script_py(
            description="Retrieve Patient resources using FHIR Patient search parameters.",
            schema=schemas["get_patient"],
            arg_lines=patient_args,
            body_lines=patient_body,
        ),
        "get_condition.py": _primitive_script_py(
            description="Retrieve Condition resources for a patient.",
            schema=schemas["get_condition"],
            arg_lines=[
                'parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")',
                'parser.add_argument("--category", help="Optional FHIR Condition category filter.")',
            ],
            body_lines=['_get("Condition", {"patient": args.patient, "category": args.category})'],
        ),
        "get_observation_labs.py": _primitive_script_py(
            description="Retrieve laboratory Observation resources for a patient and code.",
            schema=schemas["get_observation_labs"],
            arg_lines=[
                'parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")',
                'parser.add_argument("--code", required=True, help="Observation code to filter on.")',
                'parser.add_argument("--date", help="Optional FHIR date filter expression.")',
            ],
            body_lines=['_get("Observation", {"patient": args.patient, "code": args.code, "date": args.date})'],
        ),
        "get_observation_vitals.py": _primitive_script_py(
            description="Retrieve vital-sign Observation resources for a patient and category.",
            schema=schemas["get_observation_vitals"],
            arg_lines=[
                'parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")',
                'parser.add_argument("--category", required=True, help="Observation category filter, such as vital-signs.")',
                'parser.add_argument("--date", help="Optional FHIR date filter expression.")',
            ],
            body_lines=['_get("Observation", {"patient": args.patient, "category": args.category, "date": args.date})'],
        ),
        "get_medicationrequest.py": _primitive_script_py(
            description="Retrieve MedicationRequest resources for a patient.",
            schema=schemas["get_medicationrequest"],
            arg_lines=[
                'parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")',
                'parser.add_argument("--category", help="Optional MedicationRequest category filter.")',
                'parser.add_argument("--date", help="Optional FHIR date filter expression.")',
            ],
            body_lines=['_get("MedicationRequest", {"patient": args.patient, "category": args.category, "date": args.date})'],
        ),
        "get_procedure.py": _primitive_script_py(
            description="Retrieve Procedure resources for a patient.",
            schema=schemas["get_procedure"],
            arg_lines=[
                'parser.add_argument("--patient", required=True, help="Patient identifier used in the FHIR patient query parameter.")',
                'parser.add_argument("--date", required=True, help="FHIR date filter expression.")',
                'parser.add_argument("--code", help="Optional Procedure code filter.")',
            ],
            body_lines=['_get("Procedure", {"patient": args.patient, "date": args.date, "code": args.code})'],
        ),
        "post_observation_vitals.py": _primitive_script_py(
            description="Simulate posting a vital-sign Observation payload from a JSON file.",
            schema=schemas["post_observation_vitals"],
            arg_lines=['parser.add_argument("--payload-file", required=True, help="Path to a JSON file containing one Observation payload.")'],
            body_lines=['_simulate_post("Observation", args.payload_file)'],
            include_schema_in_help=True,
        ),
        "post_medicationrequest.py": _primitive_script_py(
            description="Simulate posting a MedicationRequest payload from a JSON file.",
            schema=schemas["post_medicationrequest"],
            arg_lines=['parser.add_argument("--payload-file", required=True, help="Path to a JSON file containing one MedicationRequest payload.")'],
            body_lines=['_simulate_post("MedicationRequest", args.payload_file)'],
            include_schema_in_help=True,
        ),
        "post_servicerequest.py": _primitive_script_py(
            description="Simulate posting a ServiceRequest payload from a JSON file.",
            schema=schemas["post_servicerequest"],
            arg_lines=['parser.add_argument("--payload-file", required=True, help="Path to a JSON file containing one ServiceRequest payload.")'],
            body_lines=['_simulate_post("ServiceRequest", args.payload_file)'],
            include_schema_in_help=True,
        ),
    }


def _test_sh() -> str:
    return _clean_block(
        """
        #!/usr/bin/env bash
        set -euo pipefail

        mkdir -p /logs/verifier

        extra_args=()
        if [[ -n "${VERIFIER_ERROR_ANALYSIS_FILE:-}" ]]; then
          extra_args+=(--error-analysis-file "${VERIFIER_ERROR_ANALYSIS_FILE}")
        fi

        python /tests/verify_meta_task.py \
          --submission /workspace/submission.json \
          --tasks /workspace/benchmark_tasks.json \
          --answer-key /tests/task_answer_key.json \
          --reward-file /logs/verifier/reward.txt \
          "${extra_args[@]}"
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


        def _normalize_tasks(payload):
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
                return payload["tasks"]
            raise ValueError("benchmark_tasks.json must be a list or an object with a 'tasks' list")


        def _error_analysis_rows(summary, merged_rows, submitted_by_id, answers_by_id):
            merged_by_id = {
                str(row.get("task_id", row.get("id", ""))): row
                for row in merged_rows
                if isinstance(row, dict)
            }
            shaped = []
            for result in summary.get("results", []):
                if not isinstance(result, dict):
                    continue
                if result.get("success", False):
                    continue
                task_id = str(result.get("task_id", ""))
                merged = merged_by_id.get(task_id, {})
                submitted = submitted_by_id.get(task_id, {})
                expected = answers_by_id.get(task_id, {})
                shaped.append(
                    {
                        "task_id": task_id,
                        "category": expected.get("category", ""),
                        "difficulty": expected.get("difficulty", ""),
                        "failure_reason": result.get("failure_reason", ""),
                        "expected_answer": expected.get("expected_answer", ""),
                        "final_answer": submitted.get("final_answer", ""),
                        "expected_payload": expected.get("payload"),
                        "final_payload": submitted.get("payload"),
                        "instruction": merged.get("instruction", submitted.get("instruction", "")),
                    }
                )
            return shaped


        def main() -> None:
            parser = argparse.ArgumentParser()
            parser.add_argument("--submission", type=Path, required=True)
            parser.add_argument("--tasks", type=Path, required=True)
            parser.add_argument("--answer-key", type=Path, required=True)
            parser.add_argument("--reward-file", type=Path, required=True)
            parser.add_argument("--error-analysis-file", type=Path)
            args = parser.parse_args()

            if not args.submission.exists():
                args.reward_file.write_text("0\\n", encoding="utf-8")
                print(f"missing submission file: {args.submission}")
                return

            task_payload = _normalize_tasks(_load_json(args.tasks))
            expected_ids = [row["task_id"] for row in task_payload if isinstance(row, dict)]
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
            args.reward_file.parent.mkdir(parents=True, exist_ok=True)
            results_path = args.reward_file.parent / "meta_results.json"
            results_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
            if args.error_analysis_file is not None:
                error_rows = _error_analysis_rows(summary, rows, submitted_by_id, answers_by_id)
                args.error_analysis_file.write_text(
                    json.dumps(error_rows, indent=2, ensure_ascii=False) + "\\n",
                    encoding="utf-8",
                )
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
    primitive_schemas: dict[str, dict[str, Any]],
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
    answer_key = _answer_key_payload(selected_raw_tasks)
    submission_template = _submission_template(selected_raw_tasks)

    task_dir.joinpath("instruction.md").write_text(
        _instruction_md(benchmark_payload), encoding="utf-8"
    )
    task_dir.joinpath("task.toml").write_text(
        _task_toml(selected_task_ids), encoding="utf-8"
    )
    _write_json(task_dir / "benchmark_tasks.json", benchmark_payload)

    environment_dir = task_dir / "environment"
    workspace_dir = environment_dir / "workspace"
    scripts_dir = workspace_dir / "scripts"
    primitives_dir = scripts_dir / "primitives"
    lib_dir = scripts_dir / "lib"
    primitives_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)

    environment_dir.joinpath("Dockerfile").write_text(
        _environment_dockerfile(), encoding="utf-8"
    )
    environment_dir.joinpath("docker-compose.yaml").write_text(
        _environment_compose(), encoding="utf-8"
    )
    workspace_dir.joinpath("README.md").write_text(_workspace_readme(), encoding="utf-8")
    _write_json(workspace_dir / "benchmark_tasks.json", benchmark_payload)
    _write_json(workspace_dir / "submission.json", submission_template)
    primitive_scripts = _primitive_scripts(primitive_schemas)
    (lib_dir / "fhir_common.py").write_text(_fhir_common_py(), encoding="utf-8")
    for script_name, content in primitive_scripts.items():
        primitives_dir.joinpath(script_name).write_text(content, encoding="utf-8")
    for script_name in primitive_scripts:
        (primitives_dir / script_name).chmod(0o755)

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


def main() -> None:
    args = _parse_args()
    raw_tasks = load_raw_tasks(args.input_json)
    primitive_schemas = _primitive_schemas(_load_funcs(args.funcs_json))
    selected_task_ids = _split_csv(args.selected_task_ids) or default_selected_task_ids(raw_tasks)
    selected_raw_tasks = _select_tasks(raw_tasks, selected_task_ids)

    _write_meta_task(
        selected_raw_tasks=selected_raw_tasks,
        selected_task_ids=selected_task_ids,
        primitive_schemas=primitive_schemas,
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
