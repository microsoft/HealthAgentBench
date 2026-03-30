import os
import shlex
from pathlib import Path

from harbor.agents.installed.base import ExecInput
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

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        auth_file = self._resolve_auth_file()
        await environment.exec(command="mkdir -p /tmp/codex-secrets")
        await environment.upload_file(
            source_path=auth_file,
            target_path="/tmp/codex-secrets/auth.json",
        )
        await super().run(instruction, environment, context)

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
        escaped_instruction = shlex.quote(instruction)

        if not self.model_name:
            raise ValueError("Model name is required")

        model = self.model_name.split("/")[-1]
        self._resolve_auth_file()

        env = {
            "CODEX_HOME": (EnvironmentPaths.agent_dir).as_posix(),
        }

        if openai_base_url := os.environ.get("OPENAI_BASE_URL"):
            env["OPENAI_BASE_URL"] = openai_base_url

        # Build command with optional reasoning_effort from descriptor
        cli_flags = self.build_cli_flags()
        reasoning_flag = (cli_flags + " ") if cli_flags else ""

        setup_command = """
mkdir -p /tmp/codex-secrets "$CODEX_HOME"
ln -sf /tmp/codex-secrets/auth.json "$CODEX_HOME/auth.json"
                """

        skills_command = self._build_register_skills_command()
        if skills_command:
            setup_command += f"\n{skills_command}"

        mcp_command = self._build_register_mcp_servers_command()
        if mcp_command:
            setup_command += f"\n{mcp_command}"

        return [
            ExecInput(
                command=setup_command,
                env=env,
            ),
            ExecInput(
                command=(
                    "trap 'rm -rf /tmp/codex-secrets \"$CODEX_HOME/auth.json\"' EXIT TERM INT; "
                    ". ~/.nvm/nvm.sh; "
                    "codex exec "
                    "--dangerously-bypass-approvals-and-sandbox "
                    "--skip-git-repo-check "
                    f"--model {model} "
                    "--json "
                    "--enable unified_exec "
                    f"{reasoning_flag}"
                    "-- "  # end of flags
                    f"{escaped_instruction} "
                    f"2>&1 </dev/null | stdbuf -oL tee {
                        EnvironmentPaths.agent_dir / self._OUTPUT_FILENAME
                    }"
                ),
                env=env,
            ),
        ]
