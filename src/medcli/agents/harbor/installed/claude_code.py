"""MedCLI wrapper around Harbor's Claude Code installed agent.

Auth precedence (first match wins):

1. ``CLAUDE_CODE_OAUTH_TOKEN`` env var (Claude Code OAuth — typical for
   ``claude.ai`` Max subscriptions).
2. ``ANTHROPIC_API_KEY`` (or ``ANTHROPIC_AUTH_TOKEN``) env var.
3. ``CLAUDE_CODE_USE_BEDROCK=1`` + AWS creds (Harbor's Bedrock pathway).
4. Fallback: read ``~/.claude/.credentials.json`` (or path from
   ``CLAUDE_CODE_AUTH_FILE``) and export ``CLAUDE_CODE_OAUTH_TOKEN`` from
   ``claudeAiOauth.accessToken``.

Harbor's underlying agent reads these env vars at run time and forwards them
into the container; this wrapper's job is to ensure at least one of them is
set on the host process before the run starts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from harbor.agents.installed.base import with_prompt_template
from harbor.agents.installed.claude_code import ClaudeCode as HarborClaudeCode
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class ClaudeCode(HarborClaudeCode):
    """MedCLI wrapper around Harbor's Claude Code installed agent."""

    @staticmethod
    def _resolve_auth_file() -> Path | None:
        auth_file = os.environ.get("CLAUDE_CODE_AUTH_FILE", "").strip()
        path = (
            Path(auth_file).expanduser()
            if auth_file
            else Path.home() / ".claude" / ".credentials.json"
        )
        return path if path.is_file() else None

    @classmethod
    def ensure_auth_env(cls) -> None:
        """Populate ``CLAUDE_CODE_OAUTH_TOKEN`` from the credentials file when
        no token / API key is already set in the environment. Raises if no
        usable auth source is found."""
        if any(
            os.environ.get(k, "").strip()
            for k in (
                "CLAUDE_CODE_OAUTH_TOKEN",
                "ANTHROPIC_API_KEY",
                "ANTHROPIC_AUTH_TOKEN",
            )
        ):
            return
        # Bedrock: AWS creds carry the auth implicitly.
        if (
            os.environ.get("CLAUDE_CODE_USE_BEDROCK", "").strip() == "1"
            or os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
        ):
            return
        path = cls._resolve_auth_file()
        if path is None:
            raise ValueError(
                "Claude Code auth not found. Set CLAUDE_CODE_OAUTH_TOKEN or "
                "ANTHROPIC_API_KEY, point CLAUDE_CODE_AUTH_FILE at a credentials "
                "JSON, or ensure ~/.claude/.credentials.json exists."
            )
        try:
            payload = json.loads(path.read_text())
            token = (payload.get("claudeAiOauth") or {}).get("accessToken")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            raise ValueError(
                f"Failed to parse Claude Code credentials at {path}: {exc}"
            ) from exc
        if not token:
            raise ValueError(
                f"No claudeAiOauth.accessToken in {path}. Re-run `claude login`."
            )
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = token

    @with_prompt_template
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        # Resolve auth lazily so unit tests that import this module don't
        # require a credentials file on disk.
        self.ensure_auth_env()
        await super().run(instruction, environment, context)
