"""Host-side Harbor agent wrapper for Biomni."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.agent.context import AgentContext


_DEFAULT_TIMEOUT_SECONDS = 1200
_DEFAULT_BRIDGE_SERVER_NAME = "medcli_task"


@dataclass(frozen=True)
class BiomniHostConfig:
    """Resolved host-side Biomni configuration."""

    python_executable: Path
    data_path: Path
    llm: str | None
    timeout_seconds: int
    bridge_python: Path
    repo_root: Path


@dataclass(frozen=True)
class DockerComposeAccessConfig:
    """Serializable Docker Compose access metadata for the MCP bridge."""

    project_name: str
    project_directory: str
    compose_files: list[str]
    compose_env: dict[str, str]
    main_service: str = "main"


def _sanitize_docker_compose_project_name(name: str) -> str:
    """Mirror Harbor's Docker Compose project-name sanitization."""

    lowered = name.lower()
    if not re.match(r"^[a-z0-9]", lowered):
        lowered = f"0{lowered}"
    return re.sub(r"[^a-z0-9_-]", "-", lowered)


def _env_lookup(
    name: str,
    extra_env: Mapping[str, str],
    default: str | None = None,
) -> str | None:
    """Resolve a variable from explicit agent env overrides first, then host env."""

    if name in extra_env and extra_env[name].strip():
        return extra_env[name].strip()
    value = os.environ.get(name, "").strip()
    if value:
        return value
    return default


def resolve_biomni_host_config(
    *,
    model_name: str | None,
    extra_env: Mapping[str, str],
    python_executable: str | None = None,
    data_path: str | None = None,
    timeout_seconds: int | None = None,
    bridge_python: str | None = None,
    repo_root: Path | None = None,
) -> BiomniHostConfig:
    """Resolve the host-side Biomni runtime configuration."""

    resolved_repo_root = repo_root or Path(__file__).resolve().parents[5]
    resolved_python = (
        python_executable or _env_lookup("BIOMNI_PYTHON", extra_env) or sys.executable
    )
    resolved_data_path = data_path or _env_lookup("BIOMNI_DATA_PATH", extra_env)
    if not resolved_data_path:
        raise ValueError(
            "Biomni data path is required. Set BIOMNI_DATA_PATH or pass data_path."
        )

    timeout_raw = timeout_seconds or int(
        _env_lookup(
            "BIOMNI_TIMEOUT_SECONDS",
            extra_env,
            default=str(_DEFAULT_TIMEOUT_SECONDS),
        )
        or _DEFAULT_TIMEOUT_SECONDS
    )
    resolved_llm = model_name or _env_lookup("BIOMNI_LLM", extra_env)
    resolved_bridge_python = bridge_python or sys.executable

    return BiomniHostConfig(
        python_executable=Path(resolved_python).expanduser().resolve(),
        data_path=Path(resolved_data_path).expanduser().resolve(),
        llm=resolved_llm,
        timeout_seconds=timeout_raw,
        bridge_python=Path(resolved_bridge_python).expanduser().resolve(),
        repo_root=resolved_repo_root.resolve(),
    )


def build_compose_access_config(
    environment: DockerEnvironment,
) -> DockerComposeAccessConfig:
    """Serialize the active Harbor Docker environment for external bridge access."""

    compose_env = environment._env_vars.to_env_dict(include_os_env=False)
    if environment._compose_task_env:
        compose_env.update(environment._compose_task_env)
    if environment._persistent_env:
        compose_env.update(environment._persistent_env)

    return DockerComposeAccessConfig(
        project_name=_sanitize_docker_compose_project_name(environment.session_id),
        project_directory=str(environment.environment_dir.resolve()),
        compose_files=[
            str(path.resolve()) for path in environment._docker_compose_paths
        ],
        compose_env=compose_env,
    )


def build_biomni_instruction(original_instruction: str) -> str:
    """Augment the Harbor task instruction with bridge usage guidance."""

    prefix = (
        "You are operating a live MedCLI Harbor task environment through MCP tools.\n"
        "Use the MCP tools named `workspace_read_text`, `workspace_read_json`, "
        "`workspace_list`, `container_exec`, `submission_get`, `submission_update_row`, "
        "and `workspace_write_json` to inspect the task environment and write your final "
        "results into `/workspace/submission.json`.\n"
        "Do not rely on host-local files outside the task bridge. Treat the task "
        "container as the source of truth.\n"
    )
    return f"{prefix}\n{original_instruction}"


def build_biomni_mcp_config(
    *,
    bridge_python: Path,
    bridge_script_path: Path,
    bridge_config_path: Path,
    server_name: str = _DEFAULT_BRIDGE_SERVER_NAME,
) -> dict[str, Any]:
    """Build Biomni's MCP YAML payload for the MedCLI bridge server."""

    return {
        "mcp_servers": {
            server_name: {
                "enabled": True,
                "command": [
                    str(bridge_python),
                    str(bridge_script_path),
                    "--config",
                    str(bridge_config_path),
                ],
            }
        }
    }


def build_biomni_runner_config(
    *,
    instruction: str,
    mcp_config_path: Path,
    result_path: Path,
    data_path: Path,
    llm: str | None,
) -> dict[str, Any]:
    """Build the JSON config consumed by the standalone Biomni runner."""

    payload: dict[str, Any] = {
        "instruction": instruction,
        "mcp_config_path": str(mcp_config_path),
        "result_path": str(result_path),
        "data_path": str(data_path),
    }
    if llm:
        payload["llm"] = llm
    return payload


class BiomniHostAgent(BaseAgent):
    """Run Biomni from a host-side Python environment while Harbor manages Docker."""

    _LOG_FILENAME = "biomni-host.log"
    _RUNNER_RESULT_FILENAME = "biomni-runner-result.json"
    _BRIDGE_CONFIG_FILENAME = "biomni-bridge-config.json"
    _MCP_CONFIG_FILENAME = "biomni-mcp-config.yaml"
    _RUNNER_CONFIG_FILENAME = "biomni-runner-config.json"

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        logger=None,
        extra_env: dict[str, str] | None = None,
        python_executable: str | None = None,
        data_path: str | None = None,
        timeout_seconds: int | None = None,
        bridge_python: str | None = None,
        **kwargs,
    ):
        self._extra_env = dict(extra_env or {})
        super().__init__(
            logs_dir=logs_dir, model_name=model_name, logger=logger, **kwargs
        )
        self._config = resolve_biomni_host_config(
            model_name=model_name,
            extra_env=self._extra_env,
            python_executable=python_executable,
            data_path=data_path,
            timeout_seconds=timeout_seconds,
            bridge_python=bridge_python,
        )
        self._version: str | None = None

    @staticmethod
    def name() -> str:
        return "biomni-host"

    def version(self) -> str | None:
        return self._version

    @property
    def _bridge_script_path(self) -> Path:
        return Path(__file__).with_name("biomni_bridge.py")

    @property
    def _runner_script_path(self) -> Path:
        return Path(__file__).with_name("biomni_runner.py")

    def _build_subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(self._extra_env)
        if self.model_name and "BIOMNI_LLM" not in env:
            env["BIOMNI_LLM"] = self.model_name
        env.setdefault("BIOMNI_DATA_PATH", str(self._config.data_path))
        env.setdefault("BIOMNI_TIMEOUT_SECONDS", str(self._config.timeout_seconds))
        return env

    async def _run_probe(self, command: list[str]) -> tuple[int, str]:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(self._config.repo_root),
            env=self._build_subprocess_env(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await process.communicate()
        return process.returncode or 0, stdout.decode("utf-8", errors="replace")

    async def setup(self, environment: BaseEnvironment) -> None:
        del environment
        if not self._config.python_executable.is_file():
            raise FileNotFoundError(
                f"Biomni Python executable not found: {self._config.python_executable}"
            )
        if not self._config.data_path.exists():
            raise FileNotFoundError(
                f"Biomni data path not found: {self._config.data_path}"
            )

        command = [
            str(self._config.python_executable),
            "-c",
            (
                "from biomni.agent import A1; "
                "import biomni; "
                "from biomni.version import __version__; "
                "print(__version__)"
            ),
        ]
        return_code, output = await self._run_probe(command)
        if return_code != 0:
            raise RuntimeError(
                "Failed to import Biomni from the configured host Python executable.\n"
                f"Command: {' '.join(command)}\n"
                f"Output:\n{output}"
            )
        self._version = output.strip().splitlines()[-1] if output.strip() else "unknown"

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        if not isinstance(environment, DockerEnvironment):
            raise RuntimeError(
                "BiomniHostAgent currently requires Harbor's Docker environment."
            )

        bridge_config_path = self.logs_dir / self._BRIDGE_CONFIG_FILENAME
        mcp_config_path = self.logs_dir / self._MCP_CONFIG_FILENAME
        runner_config_path = self.logs_dir / self._RUNNER_CONFIG_FILENAME
        runner_result_path = self.logs_dir / self._RUNNER_RESULT_FILENAME
        log_path = self.logs_dir / self._LOG_FILENAME

        bridge_config = build_compose_access_config(environment)
        bridge_config_path.write_text(
            json.dumps(asdict(bridge_config), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        mcp_config = build_biomni_mcp_config(
            bridge_python=self._config.bridge_python,
            bridge_script_path=self._bridge_script_path,
            bridge_config_path=bridge_config_path,
        )
        mcp_config_path.write_text(
            yaml.safe_dump(mcp_config, sort_keys=False),
            encoding="utf-8",
        )

        runner_config = build_biomni_runner_config(
            instruction=build_biomni_instruction(instruction),
            mcp_config_path=mcp_config_path,
            result_path=runner_result_path,
            data_path=self._config.data_path,
            llm=self._config.llm,
        )
        runner_config_path.write_text(
            json.dumps(runner_config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        command = [
            str(self._config.python_executable),
            str(self._runner_script_path),
            "--config",
            str(runner_config_path),
        ]

        env = self._build_subprocess_env()
        process: asyncio.subprocess.Process | None = None
        with log_path.open("w", encoding="utf-8") as log_handle:
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=str(self._config.repo_root),
                    env=env,
                    stdout=log_handle,
                    stderr=asyncio.subprocess.STDOUT,
                )
                await asyncio.wait_for(
                    process.wait(),
                    timeout=self._config.timeout_seconds,
                )
            except asyncio.TimeoutError:
                if process is not None and process.returncode is None:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=10)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                raise
            finally:
                log_handle.flush()

        result_payload: dict[str, Any] = {}
        if runner_result_path.exists():
            result_payload = json.loads(runner_result_path.read_text(encoding="utf-8"))

        context.metadata = {
            "biomni_python": str(self._config.python_executable),
            "biomni_data_path": str(self._config.data_path),
            "bridge_config_path": str(bridge_config_path),
            "mcp_config_path": str(mcp_config_path),
            "runner_result_path": str(runner_result_path),
            "log_path": str(log_path),
            "result": result_payload,
        }

        if process is None:
            raise RuntimeError("Biomni subprocess was not started.")
        if process.returncode != 0:
            raise RuntimeError(
                f"Biomni subprocess exited with code {process.returncode}. "
                f"See {log_path} and {runner_result_path} for details."
            )
