"""Standalone MCP bridge that exposes a Harbor Docker task to Biomni."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from mcp.server.fastmcp import FastMCP


@dataclass(frozen=True)
class DockerComposeAccessConfig:
    """Bridge runtime information for the active Harbor Docker Compose project."""

    project_name: str
    project_directory: str
    compose_files: list[str]
    compose_env: dict[str, str]
    main_service: str = "main"


def update_submission_payload(
    submission_payload: Any,
    *,
    task_id: str,
    final_answer: str | None = None,
    payload_json: str | None = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Update one submission row in-memory."""

    rows: list[dict[str, Any]]
    wrapped = False
    if isinstance(submission_payload, list):
        rows = [dict(row) for row in submission_payload if isinstance(row, dict)]
    elif isinstance(submission_payload, dict) and isinstance(
        submission_payload.get("results"), list
    ):
        rows = [
            dict(row) for row in submission_payload["results"] if isinstance(row, dict)
        ]
        wrapped = True
    else:
        raise ValueError(
            "submission.json must be a list or an object with a 'results' list"
        )

    found = False
    for row in rows:
        if str(row.get("task_id", "")) != task_id:
            continue
        if final_answer is not None:
            row["final_answer"] = final_answer
        if payload_json is not None:
            row["payload"] = json.loads(payload_json)
        found = True
        break

    if not found:
        raise KeyError(f"Task ID not found in submission payload: {task_id}")

    if wrapped:
        return {"results": rows}
    return rows


class DockerComposeBridge:
    """Thin Docker Compose client for the active Harbor task environment."""

    def __init__(self, config: DockerComposeAccessConfig):
        self.config = config

    @property
    def _base_command(self) -> list[str]:
        command = [
            "docker",
            "compose",
            "--project-name",
            self.config.project_name,
            "--project-directory",
            self.config.project_directory,
        ]
        for compose_file in self.config.compose_files:
            command.extend(["-f", compose_file])
        return command

    def _run_compose(
        self,
        args: list[str],
        *,
        check: bool = False,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(self.config.compose_env)
        process = subprocess.run(
            [*self._base_command, *args],
            input=input_text,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        if check and process.returncode != 0:
            raise RuntimeError(
                f"Docker Compose command failed with code {process.returncode}: "
                f"{' '.join([*self._base_command, *args])}\n"
                f"stdout:\n{process.stdout}\n"
                f"stderr:\n{process.stderr}"
            )
        return process

    def exec(
        self,
        command: str,
        *,
        cwd: str | None = None,
        user: str | None = None,
    ) -> dict[str, Any]:
        args = ["exec", "-T"]
        if cwd:
            args.extend(["-w", cwd])
        if user:
            args.extend(["-u", user])
        args.extend([self.config.main_service, "bash", "-lc", command])
        result = self._run_compose(args)
        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def read_text(self, path: str) -> str:
        quoted = json.dumps(path)
        command = (
            "python - <<'PY'\n"
            "from pathlib import Path\n"
            f"path = Path({quoted})\n"
            "print(path.read_text(encoding='utf-8'), end='')\n"
            "PY"
        )
        result = self.exec(command)
        if result["return_code"] != 0:
            raise RuntimeError(
                f"Failed to read {path}\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
            )
        return str(result["stdout"])

    def read_json(self, path: str) -> Any:
        return json.loads(self.read_text(path))

    def list_dir(self, path: str) -> dict[str, Any]:
        quoted = json.dumps(path)
        command = (
            "python - <<'PY'\n"
            "import json\n"
            "from pathlib import Path\n"
            f"root = Path({quoted})\n"
            "payload = {\n"
            "  'path': str(root),\n"
            "  'entries': [\n"
            "    {\n"
            "      'name': child.name,\n"
            "      'path': str(child),\n"
            "      'is_dir': child.is_dir(),\n"
            "      'is_file': child.is_file(),\n"
            "    }\n"
            "    for child in sorted(root.iterdir(), key=lambda item: item.name)\n"
            "  ],\n"
            "}\n"
            "print(json.dumps(payload, ensure_ascii=False))\n"
            "PY"
        )
        result = self.exec(command)
        if result["return_code"] != 0:
            raise RuntimeError(
                f"Failed to list {path}\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
            )
        return json.loads(str(result["stdout"]))

    def _mkdir_parent(self, path: str) -> None:
        parent = str(PurePosixPath(path).parent)
        if not parent or parent == ".":
            return
        result = self.exec(f"mkdir -p {json.dumps(parent)}")
        if result["return_code"] != 0:
            raise RuntimeError(
                f"Failed to create parent directory for {path}\n"
                f"stdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
            )

    def write_text(self, path: str, content: str) -> dict[str, Any]:
        self._mkdir_parent(path)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        try:
            result = self._run_compose(
                ["cp", str(temp_path), f"{self.config.main_service}:{path}"],
                check=True,
            )
        finally:
            temp_path.unlink(missing_ok=True)
        return {
            "path": path,
            "return_code": result.returncode,
        }

    def write_json(self, path: str, payload: Any) -> dict[str, Any]:
        content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        return self.write_text(path, content)

    def update_submission_row(
        self,
        *,
        task_id: str,
        final_answer: str | None = None,
        payload_json: str | None = None,
        path: str = "/workspace/submission.json",
    ) -> dict[str, Any]:
        payload = self.read_json(path)
        updated = update_submission_payload(
            payload,
            task_id=task_id,
            final_answer=final_answer,
            payload_json=payload_json,
        )
        self.write_json(path, updated)
        return {
            "path": path,
            "task_id": task_id,
            "updated_final_answer": final_answer is not None,
            "updated_payload": payload_json is not None,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = DockerComposeAccessConfig(
        **json.loads(args.config.read_text(encoding="utf-8"))
    )
    bridge = DockerComposeBridge(config)
    server = FastMCP("medcli-task-bridge")

    @server.tool(
        description="Run a shell command inside the Harbor task main container."
    )
    def container_exec(command: str, cwd: str | None = None) -> dict[str, Any]:
        return bridge.exec(command, cwd=cwd)

    @server.tool(
        description="List entries under a path inside the Harbor task main container."
    )
    def workspace_list(path: str = "/workspace") -> dict[str, Any]:
        return bridge.list_dir(path)

    @server.tool(
        description="Read a UTF-8 text file from the Harbor task main container."
    )
    def workspace_read_text(path: str) -> str:
        return bridge.read_text(path)

    @server.tool(description="Read a JSON file from the Harbor task main container.")
    def workspace_read_json(path: str) -> Any:
        return bridge.read_json(path)

    @server.tool(
        description="Write a UTF-8 text file into the Harbor task main container."
    )
    def workspace_write_text(path: str, content: str) -> dict[str, Any]:
        return bridge.write_text(path, content)

    @server.tool(description="Write a JSON file into the Harbor task main container.")
    def workspace_write_json(path: str, payload: Any) -> dict[str, Any]:
        return bridge.write_json(path, payload)

    @server.tool(
        description="Read /workspace/submission.json or another submission-style JSON file."
    )
    def submission_get(path: str = "/workspace/submission.json") -> Any:
        return bridge.read_json(path)

    @server.tool(
        description=(
            "Update one row in /workspace/submission.json by task_id. "
            "Pass payload_json='null' to clear the payload."
        )
    )
    def submission_update_row(
        task_id: str,
        final_answer: str | None = None,
        payload_json: str | None = None,
        path: str = "/workspace/submission.json",
    ) -> dict[str, Any]:
        return bridge.update_submission_row(
            task_id=task_id,
            final_answer=final_answer,
            payload_json=payload_json,
            path=path,
        )

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
