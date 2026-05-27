"""MedCLI wrapper around Harbor's upstreamed GitHub Copilot CLI agent.

Adds strict host-side auth resolution: before delegating to the parent's
``run()``, this exports ``GITHUB_TOKEN`` from the first of
``COPILOT_GITHUB_TOKEN`` / ``GH_TOKEN`` / ``GITHUB_TOKEN`` that's set on
the host, or from ``gh auth token``. Raises if none of those work, so a
missing token fails fast on the host instead of inside the container.
"""

from __future__ import annotations

import os
import subprocess

from harbor.agents.installed.copilot_cli import CopilotCli as HarborCopilotCli
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class CopilotCli(HarborCopilotCli):
    """MedCLI wrapper around Harbor's Copilot CLI installed agent."""

    @staticmethod
    def _resolve_auth_token() -> str:
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

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        os.environ.setdefault("GITHUB_TOKEN", self._resolve_auth_token())
        await super().run(instruction, environment, context)
