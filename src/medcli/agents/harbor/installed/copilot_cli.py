"""Harbor installed-agent wrapper for GitHub Copilot CLI."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from harbor.agents.installed.base import BaseInstalledAgent, CliFlag, with_prompt_template
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trajectories import (
    Agent,
    FinalMetrics,
    Metrics,
    Observation,
    ObservationResult,
    Step,
    ToolCall,
    Trajectory,
)
from harbor.models.trial.paths import EnvironmentPaths
from harbor.utils.trajectory_utils import format_trajectory_json


class CopilotCli(BaseInstalledAgent):
    """Run GitHub Copilot CLI inside a Harbor task environment."""

    SUPPORTS_ATIF: bool = True
    _OUTPUT_FILENAME = "copilot-cli.txt"

    CLI_FLAGS = [
        CliFlag(
            "reasoning_effort",
            cli="--reasoning-effort",
            type="enum",
            choices=["low", "medium", "high", "xhigh"],
        )
    ]

    @staticmethod
    def name() -> str:
        return "copilot-cli"

    def get_version_command(self) -> str | None:
        return 'if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh"; fi; copilot version'

    async def install(self, environment: BaseEnvironment) -> None:
        await self.exec_as_root(
            environment,
            command=(
                "if ldd --version 2>&1 | grep -qi musl || [ -f /etc/alpine-release ]; then"
                "  apk add --no-cache bash curl nodejs npm;"
                " elif command -v apt-get >/dev/null 2>&1; then"
                "  apt-get update && apt-get install -y bash curl ca-certificates;"
                " elif command -v yum >/dev/null 2>&1; then"
                "  yum install -y bash curl ca-certificates;"
                " else"
                '  echo "No supported package manager found for Copilot CLI setup" >&2; exit 1;'
                " fi"
            ),
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                "if ldd --version 2>&1 | grep -qi musl || [ -f /etc/alpine-release ]; then"
                "  npm install -g @github/copilot@latest;"
                " else"
                "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash && "
                '  export NVM_DIR="$HOME/.nvm" && '
                '  . "$NVM_DIR/nvm.sh" && '
                "  nvm install 22 && nvm alias default 22 && "
                "  npm install -g @github/copilot@latest;"
                " fi && "
                'if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh"; fi; '
                "copilot version"
            ),
        )

    @property
    def _trajectory_path(self) -> PurePosixPath:
        return PurePosixPath(EnvironmentPaths.agent_dir / "trajectory.json")

    def populate_context_post_run(self, context: AgentContext) -> None:
        """Convert Copilot session-state into Harbor's ATIF trajectory format."""
        try:
            session_dir = self._get_session_dir()
        except OSError as exc:
            print(f"Failed to inspect Copilot session directory: {exc}")
            return

        if not session_dir:
            print("No Copilot session directory found")
            return

        try:
            trajectory = self._convert_events_to_trajectory(session_dir)
        except Exception as exc:
            print(f"Failed to convert Copilot events to trajectory: {exc}")
            return

        if not trajectory:
            print("Failed to convert Copilot session to trajectory")
            return

        trajectory_path = self.logs_dir / "trajectory.json"
        try:
            trajectory_path.write_text(format_trajectory_json(trajectory.to_json_dict()))
        except OSError as exc:
            print(f"Failed to write trajectory file {trajectory_path}: {exc}")
            return

        if trajectory.final_metrics:
            metrics = trajectory.final_metrics
            context.cost_usd = metrics.total_cost_usd
            context.n_input_tokens = metrics.total_prompt_tokens or 0
            context.n_cache_tokens = metrics.total_cached_tokens or 0
            context.n_output_tokens = metrics.total_completion_tokens or 0

    def _get_session_dir(self) -> Path | None:
        session_root = self.logs_dir / ".copilot" / "session-state"
        if not session_root.exists():
            return None

        session_dirs = [path for path in session_root.iterdir() if path.is_dir()]
        if not session_dirs:
            return None

        if len(session_dirs) != 1:
            session_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        return session_dirs[0]

    @staticmethod
    def _stringify_result_content(result: Any) -> str | None:
        if result is None:
            return None
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            for key in ("content", "detailedContent", "textResultForLlm", "sessionLog"):
                value = result.get(key)
                if isinstance(value, str) and value:
                    return value
            return json.dumps(result, ensure_ascii=False)
        return str(result)

    def _finalize_agent_step(
        self,
        step_id: int,
        pending_step: dict[str, Any],
        current_model: str | None,
    ) -> Step:
        tool_calls = pending_step.get("tool_calls") or None
        observation_results = pending_step.get("observation_results") or None
        output_tokens = pending_step.get("output_tokens")
        metrics = None
        if isinstance(output_tokens, int):
            metrics = Metrics(completion_tokens=output_tokens)

        step = Step(
            step_id=step_id,
            timestamp=pending_step.get("timestamp"),
            source="agent",
            message=pending_step.get("message", ""),
            reasoning_content=pending_step.get("reasoning_content"),
            model_name=current_model or self.model_name,
            reasoning_effort=self._resolved_flags.get("reasoning_effort"),
            tool_calls=tool_calls,
            observation=Observation(results=observation_results)
            if observation_results
            else None,
            metrics=metrics,
            extra=pending_step.get("extra"),
        )
        return step

    def _convert_events_to_trajectory(self, session_dir: Path) -> Trajectory | None:
        events_path = session_dir / "events.jsonl"
        if not events_path.exists():
            print(f"No Copilot events.jsonl found in {session_dir}")
            return None

        raw_events: list[dict[str, Any]] = []
        with events_path.open() as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    raw_events.append(json.loads(stripped))
                except json.JSONDecodeError as exc:
                    print(f"Skipping malformed Copilot JSONL line in {events_path}: {exc}")

        if not raw_events:
            return None

        session_start = next(
            (event for event in raw_events if event.get("type") == "session.start"),
            None,
        )
        shutdown_event = next(
            (event for event in reversed(raw_events) if event.get("type") == "session.shutdown"),
            None,
        )

        session_data = session_start.get("data", {}) if isinstance(session_start, dict) else {}
        session_id = session_data.get("sessionId") or session_dir.name
        current_model = session_data.get("selectedModel") or self.model_name
        agent_version = session_data.get("copilotVersion") or self.version() or "unknown"
        agent_extra = {
            key: value
            for key, value in session_data.items()
            if key
            not in {"sessionId", "version", "producer", "copilotVersion", "startTime", "selectedModel"}
        } or None

        steps: list[Step] = []
        pending_agent_step: dict[str, Any] | None = None

        for event in raw_events:
            event_type = event.get("type")
            data = event.get("data", {})
            timestamp = event.get("timestamp")

            if event_type == "session.model_change":
                new_model = data.get("newModel")
                if isinstance(new_model, str) and new_model:
                    current_model = new_model
                continue

            if event_type == "user.message":
                if pending_agent_step:
                    steps.append(
                        self._finalize_agent_step(len(steps) + 1, pending_agent_step, current_model)
                    )
                    pending_agent_step = None

                message = data.get("transformedContent") or data.get("content")
                if not isinstance(message, str):
                    message = json.dumps(message, ensure_ascii=False)
                steps.append(
                    Step(
                        step_id=len(steps) + 1,
                        timestamp=timestamp,
                        source="user",
                        message=message,
                    )
                )
                continue

            if event_type == "assistant.message":
                if pending_agent_step:
                    steps.append(
                        self._finalize_agent_step(len(steps) + 1, pending_agent_step, current_model)
                    )

                tool_requests = data.get("toolRequests") or []
                tool_calls: list[ToolCall] = []
                for tool_request in tool_requests:
                    tool_call_id = tool_request.get("toolCallId")
                    tool_name = tool_request.get("name")
                    if not isinstance(tool_call_id, str) or not isinstance(tool_name, str):
                        continue
                    arguments = tool_request.get("arguments")
                    if not isinstance(arguments, dict):
                        arguments = {"value": arguments}
                    tool_calls.append(
                        ToolCall(
                            tool_call_id=tool_call_id,
                            function_name=tool_name,
                            arguments=arguments,
                        )
                    )

                pending_agent_step = {
                    "timestamp": timestamp,
                    "message": data.get("content", ""),
                    "reasoning_content": data.get("reasoningText"),
                    "tool_calls": tool_calls,
                    "observation_results": [],
                    "output_tokens": data.get("outputTokens"),
                    "extra": {
                        key: data.get(key)
                        for key in ("messageId", "interactionId", "phase")
                        if data.get(key) is not None
                    }
                    or None,
                }
                continue

            if event_type == "tool.execution_complete" and pending_agent_step:
                result_data = data.get("result")
                content = self._stringify_result_content(result_data)
                pending_agent_step["observation_results"].append(
                    ObservationResult(
                        source_call_id=data.get("toolCallId"),
                        content=content,
                    )
                )
                continue

            if event_type == "session.shutdown":
                if pending_agent_step:
                    steps.append(
                        self._finalize_agent_step(len(steps) + 1, pending_agent_step, current_model)
                    )
                    pending_agent_step = None
                continue

        if pending_agent_step:
            steps.append(
                self._finalize_agent_step(len(steps) + 1, pending_agent_step, current_model)
            )

        if not steps:
            print("No valid steps produced from Copilot session")
            return None

        final_metrics = None
        shutdown_data = shutdown_event.get("data", {}) if isinstance(shutdown_event, dict) else {}
        model_metrics = shutdown_data.get("modelMetrics")
        if isinstance(model_metrics, dict):
            aggregate_prompt_tokens = 0
            aggregate_completion_tokens = 0
            aggregate_cached_tokens = 0
            saw_usage = False
            for metrics in model_metrics.values():
                usage = metrics.get("usage") if isinstance(metrics, dict) else None
                if not isinstance(usage, dict):
                    continue
                saw_usage = True
                aggregate_prompt_tokens += int(usage.get("inputTokens") or 0)
                aggregate_completion_tokens += int(usage.get("outputTokens") or 0)
                aggregate_cached_tokens += int(usage.get("cacheReadTokens") or 0)

            final_metrics = FinalMetrics(
                total_prompt_tokens=aggregate_prompt_tokens if saw_usage else None,
                total_completion_tokens=aggregate_completion_tokens if saw_usage else None,
                total_cached_tokens=aggregate_cached_tokens if saw_usage else None,
                total_steps=len(steps),
                extra={
                    key: value
                    for key, value in shutdown_data.items()
                    if key not in {"modelMetrics"}
                }
                or None,
            )

        return Trajectory(
            session_id=session_id,
            agent=Agent(
                name=self.name(),
                version=agent_version,
                model_name=current_model,
                extra=agent_extra,
            ),
            steps=steps,
            final_metrics=final_metrics,
        )

    def _resolve_auth_token(self) -> str:
        for env_var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
            token = os.environ.get(env_var, "").strip()
            if token:
                return token

        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise ValueError(
                "GitHub Copilot CLI requires COPILOT_GITHUB_TOKEN, GH_TOKEN, "
                "GITHUB_TOKEN, or a working gh auth login. The gh CLI is not installed."
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else "gh auth token failed"
            raise ValueError(
                "GitHub Copilot CLI requires COPILOT_GITHUB_TOKEN, GH_TOKEN, "
                "GITHUB_TOKEN, or a working gh auth login. "
                f"`gh auth token` failed: {stderr}"
            ) from exc

        token = result.stdout.strip()
        if not token:
            raise ValueError(
                "GitHub Copilot CLI requires COPILOT_GITHUB_TOKEN, GH_TOKEN, "
                "GITHUB_TOKEN, or a working gh auth login. `gh auth token` returned no token."
            )

        return token

    @with_prompt_template
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        escaped_instruction = shlex.quote(instruction)

        if not self.model_name or not self.model_name.strip():
            raise ValueError("Model name is required")

        model = shlex.quote(self.model_name.split("/")[-1])
        env = {
            "GH_TOKEN": self._resolve_auth_token(),
            "COPILOT_HOME": "/logs/agent/.copilot",
        }

        cli_flags = self.build_cli_flags()
        extra_flags = f"{cli_flags} " if cli_flags else ""

        await self.exec_as_agent(
            environment,
            command=(
                "mkdir -p /logs/agent/.copilot /logs/agent && "
                'if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh"; fi; '
                "copilot "
                f"--model {model} "
                "--output-format text "
                "--yolo "
                "--no-ask-user "
                "--no-custom-instructions "
                f"{extra_flags}"
                f"-p {escaped_instruction} "
                f"2>&1 </dev/null | stdbuf -oL tee {EnvironmentPaths.agent_dir / self._OUTPUT_FILENAME}; "
                'status=${PIPESTATUS[0]}; '
                'chmod -R a+rX "$COPILOT_HOME" >/dev/null 2>&1 || true; '
                "exit $status"
            ),
            env=env,
        )
