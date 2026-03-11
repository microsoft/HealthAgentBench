import os
import shlex

from harbor.agents.installed.base import ExecInput
from harbor.agents.installed.codex import Codex as HarborCodex
from harbor.models.trial.paths import EnvironmentPaths


class Codex(HarborCodex):
    """MedCLI wrapper around Harbor's Codex installed agent."""

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
        escaped_instruction = shlex.quote(instruction)

        if not self.model_name:
            raise ValueError("Model name is required")

        model = self.model_name.split("/")[-1]
        codex_auth_json = os.environ.get("CODEX_AUTH_JSON", "").strip()
        if not codex_auth_json:
            raise ValueError(
                "CODEX_AUTH_JSON is required for Harbor Codex runs. "
                "Export it before invoking Harbor."
            )

        env = {
            "CODEX_AUTH_JSON": codex_auth_json,
            "CODEX_HOME": (EnvironmentPaths.agent_dir).as_posix(),
        }

        if openai_base_url := os.environ.get("OPENAI_BASE_URL"):
            env["OPENAI_BASE_URL"] = openai_base_url

        # Build command with optional reasoning_effort from descriptor
        cli_flags = self.build_cli_flags()
        reasoning_flag = (cli_flags + " ") if cli_flags else ""

        setup_command = """
mkdir -p /tmp/codex-secrets
printf '%s' "$CODEX_AUTH_JSON" > /tmp/codex-secrets/auth.json
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
