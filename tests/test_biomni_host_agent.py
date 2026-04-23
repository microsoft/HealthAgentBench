from __future__ import annotations

import json
from pathlib import Path

import yaml

from medcli.agents.harbor.host.biomni import (
    BiomniHostConfig,
    build_biomni_instruction,
    build_biomni_mcp_config,
    build_biomni_runner_config,
    resolve_biomni_host_config,
)
from medcli.agents.harbor.host.biomni_bridge import update_submission_payload
from medcli.agents.harbor.host.biomni_runner import sanitize_sys_path_for_biomni


def test_resolve_biomni_host_config_prefers_explicit_env(tmp_path: Path) -> None:
    config = resolve_biomni_host_config(
        model_name="job-model",
        extra_env={
            "BIOMNI_PYTHON": "/tmp/biomni-python",
            "BIOMNI_DATA_PATH": str(tmp_path / "data"),
            "BIOMNI_TIMEOUT_SECONDS": "321",
        },
        repo_root=tmp_path,
        bridge_python="/tmp/bridge-python",
    )

    assert isinstance(config, BiomniHostConfig)
    assert config.python_executable == Path("/tmp/biomni-python")
    assert config.data_path == tmp_path / "data"
    assert config.llm == "job-model"
    assert config.timeout_seconds == 321
    assert config.bridge_python == Path("/tmp/bridge-python")
    assert config.repo_root == tmp_path


def test_build_biomni_instruction_mentions_submission_tools() -> None:
    instruction = build_biomni_instruction("Solve the task.")

    assert "submission_update_row" in instruction
    assert "/workspace/submission.json" in instruction
    assert instruction.endswith("Solve the task.")


def test_build_biomni_mcp_config_contains_bridge_command(tmp_path: Path) -> None:
    payload = build_biomni_mcp_config(
        bridge_python=tmp_path / ".venv/bin/python",
        bridge_script_path=tmp_path / "src/bridge.py",
        bridge_config_path=tmp_path / "bridge.json",
    )

    command = payload["mcp_servers"]["medcli_task"]["command"]
    assert command == [
        str(tmp_path / ".venv/bin/python"),
        str(tmp_path / "src/bridge.py"),
        "--config",
        str(tmp_path / "bridge.json"),
    ]
    dumped = yaml.safe_dump(payload, sort_keys=False)
    assert "mcp_servers:" in dumped


def test_build_biomni_runner_config_serializes_expected_fields(tmp_path: Path) -> None:
    payload = build_biomni_runner_config(
        instruction="Inspect /workspace",
        mcp_config_path=tmp_path / "mcp.yaml",
        result_path=tmp_path / "result.json",
        data_path=tmp_path / "data",
        llm="gpt-test",
    )

    assert payload == {
        "instruction": "Inspect /workspace",
        "mcp_config_path": str(tmp_path / "mcp.yaml"),
        "result_path": str(tmp_path / "result.json"),
        "data_path": str(tmp_path / "data"),
        "llm": "gpt-test",
    }


def test_update_submission_payload_updates_list_row() -> None:
    payload = [
        {"task_id": "task1", "final_answer": "", "payload": None},
        {"task_id": "task2", "final_answer": "old", "payload": {"a": 1}},
    ]

    updated = update_submission_payload(
        payload,
        task_id="task2",
        final_answer="new-answer",
        payload_json=json.dumps({"b": 2}),
    )

    assert updated[1]["final_answer"] == "new-answer"
    assert updated[1]["payload"] == {"b": 2}


def test_update_submission_payload_updates_wrapped_results() -> None:
    payload = {
        "results": [
            {"task_id": "task1", "final_answer": "", "payload": None},
        ]
    }

    updated = update_submission_payload(
        payload,
        task_id="task1",
        payload_json="null",
    )

    assert updated == {
        "results": [
            {"task_id": "task1", "final_answer": "", "payload": None},
        ]
    }


def test_sanitize_sys_path_for_biomni_removes_shadowing_script_dir(
    tmp_path: Path,
) -> None:
    script_path = tmp_path / "src/medcli/agents/harbor/host/biomni_runner.py"
    script_path.parent.mkdir(parents=True)
    script_path.write_text("", encoding="utf-8")

    sys_path = [
        str(script_path.parent),
        "/opt/biomni-site-packages",
        "",
    ]

    sanitized = sanitize_sys_path_for_biomni(script_path, sys_path)

    assert str(script_path.parent) not in sanitized
    assert "/opt/biomni-site-packages" in sanitized
