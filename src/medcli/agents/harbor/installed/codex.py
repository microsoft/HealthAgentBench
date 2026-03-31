import os
import shlex
from pathlib import Path

from harbor.agents.installed.base import with_prompt_template
from harbor.agents.installed.codex import Codex as HarborCodex
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths


class Codex(HarborCodex):
    """MedCLI wrapper around Harbor's Codex installed agent."""

    @staticmethod
    def _resolve_auth_file() -> Path:
        auth_file = os.environ.get("CODEX_AUTH_FILE", "").strip()
        path = Path(auth_file).expanduser() if auth_file else Path.home() / ".codex" / "auth.json"
        if not path.is_file():
            raise ValueError(
                "Codex auth file not found. Expected ~/.codex/auth.json or set CODEX_AUTH_FILE."
            )
        return path

    @with_prompt_template
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        escaped_instruction = shlex.quote(instruction)

        if not self.model_name:
            raise ValueError("Model name is required")

        model = self.model_name.split("/")[-1]
        env = {
            "CODEX_HOME": EnvironmentPaths.agent_dir.as_posix(),
        }

        codex_auth_json = os.environ.get("CODEX_AUTH_JSON", "").strip()
        codex_task_toml = os.environ.get("CODEX_TASK_TOML", "").strip()
        azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()

        # Determine authentication mode
        if codex_auth_json:
            auth_file = self._resolve_auth_file()
            await self.exec_as_agent(environment, command="mkdir -p /tmp/codex-secrets")
            await environment.upload_file(
                source_path=auth_file,
                target_path="/tmp/codex-secrets/auth.json",
            )
            env["CODEX_AUTH_JSON"] = codex_auth_json
            setup_command = """
mkdir -p "$CODEX_HOME"
ln -sf /tmp/codex-secrets/auth.json "$CODEX_HOME/auth.json"
"""

        elif azure_openai_api_key and codex_task_toml:
            env["AZURE_OPENAI_API_KEY"] = azure_openai_api_key
            env["CODEX_TASK_TOML"] = codex_task_toml
            setup_command = """
mkdir -p /tmp/codex-secrets "$CODEX_HOME"
printf '%s' "$CODEX_TASK_TOML" > /tmp/codex-secrets/config.toml
ln -sf /tmp/codex-secrets/config.toml "$CODEX_HOME/config.toml"
"""

        else:
            raise ValueError(
                "Either CODEX_AUTH_JSON or AZURE_OPENAI_API_KEY and CODEX_TASK_TOML are required for Harbor Codex runs. "
                "Export them before invoking Harbor."
            )

        # Add optional OPENAI_BASE_URL if provided
        if openai_base_url := os.environ.get("OPENAI_BASE_URL"):
            env["OPENAI_BASE_URL"] = openai_base_url

        # Build command with optional reasoning_effort from descriptor
        cli_flags = self.build_cli_flags()
        reasoning_flag = (cli_flags + " ") if cli_flags else ""



        skills_command = self._build_register_skills_command()
        if skills_command:
            setup_command += f"\n{skills_command}"

        mcp_command = self._build_register_mcp_servers_command()
        if mcp_command:
            setup_command += f"\n{mcp_command}"

        await self.exec_as_agent(
            environment,
            command=setup_command,
            env=env,
        )
        try:
            await self.exec_as_agent(
                environment,
                command=(
                    "trap 'rm -rf /tmp/codex-secrets \"$CODEX_HOME/auth.json\"' EXIT TERM INT; "
                    "if [ -s ~/.nvm/nvm.sh ]; then . ~/.nvm/nvm.sh; fi; "
                    "codex exec "
                    "--dangerously-bypass-approvals-and-sandbox "
                    "--skip-git-repo-check "
                    f"--model {model} "
                    "--json "
                    "--enable unified_exec "
                    f"{reasoning_flag}"
                    "-- "  # end of flags
                    f"{escaped_instruction} "
                    f"2>&1 </dev/null | tee {EnvironmentPaths.agent_dir / self._OUTPUT_FILENAME}"
                ),
                env=env,
            )
        finally:
            try:
                await self.exec_as_agent(
                    environment,
                    command='rm -rf /tmp/codex-secrets "$CODEX_HOME/auth.json"',
                    env={"CODEX_HOME": EnvironmentPaths.agent_dir.as_posix()},
                )
            except Exception:
                pass
