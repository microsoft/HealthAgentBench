"""Harbor installed-agent wrapper for GitHub Copilot CLI."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from harbor.agents.installed.base import BaseInstalledAgent, CliFlag, ExecInput
from harbor.models.agent.context import AgentContext


class CopilotCli(BaseInstalledAgent):
    """Run GitHub Copilot CLI inside a Harbor task environment."""

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

    @property
    def _install_agent_template_path(self) -> Path:
        return Path(__file__).parent / "install-copilot-cli.sh.j2"

    def get_version_command(self) -> str | None:
        return ". ~/.nvm/nvm.sh; copilot version"

    def populate_context_post_run(self, context: AgentContext) -> None:
        """Copilot v1 does not export structured trajectory data."""

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

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
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

        return [
            ExecInput(
                command=(
                    "mkdir -p /logs/agent/.copilot /logs/agent "
                    "&& . ~/.nvm/nvm.sh; "
                    "copilot "
                    f"--model {model} "
                    "--output-format text "
                    "--yolo "
                    "--no-ask-user "
                    "--no-custom-instructions "
                    f"{extra_flags}"
                    f"-p {escaped_instruction} "
                    f"2>&1 </dev/null | stdbuf -oL tee /logs/agent/copilot-cli.txt"
                ),
                env=env,
            )
        ]
