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
        codex_task_toml = os.environ.get("CODEX_TASK_TOML", "").strip()
        azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()

        # Determine authentication mode
        if codex_auth_json:
            env = {
                "CODEX_AUTH_JSON": codex_auth_json,
                "CODEX_HOME": (EnvironmentPaths.agent_dir).as_posix(),
            }
            setup_command = """
            mkdir -p /tmp/codex-secrets
            printf '%s' "$CODEX_AUTH_JSON" > /tmp/codex-secrets/auth.json
            ln -sf /tmp/codex-secrets/auth.json "$CODEX_HOME/auth.json"
                            """

        elif azure_openai_api_key and codex_task_toml:
            env = {
                "AZURE_OPENAI_API_KEY": azure_openai_api_key,
                "CODEX_TASK_TOML": codex_task_toml,
                "CODEX_HOME": (EnvironmentPaths.agent_dir).as_posix(),
            }
            setup_command = """
            mkdir -p /tmp/codex-secrets
            printf '%s' "$CODEX_TASK_TOML" > /tmp/codex-secrets/config.toml
            ln -sf /tmp/codex-secrets/config.toml "$CODEX_HOME/config.toml"
            export AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY"
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

        return [
            ExecInput(
                command=setup_command,
                env=env,
            ),
            ExecInput(
                command=(
                    ". ~/.nvm/nvm.sh; "
                    "for attempt in 1 2 3 4 5; do "
                    "codex exec "
                    "--dangerously-bypass-approvals-and-sandbox "
                    "--skip-git-repo-check "
                    f"--model {model} "
                    "--json "
                    "--enable unified_exec "
                    f"{reasoning_flag}"
                    "-- "  # end of flags
                    f"{escaped_instruction} "
                    f"2>&1 | tee {
                        EnvironmentPaths.agent_dir / self._OUTPUT_FILENAME
                    }; "
                    "exit_code=$?; "
                    "echo \"[ATTEMPT $attempt] codex exit code: $exit_code\" >> {agent_log}; "
                    "[ $exit_code -eq 0 ] && break; "
                    "sleep $((attempt * 2)); "
                    "done; "
                    "[ $exit_code -ne 0 ] && echo \"[FINAL] All 3 attempts failed with exit code $exit_code\" >> {agent_log}"
                ).format(
                    agent_log=EnvironmentPaths.agent_dir / "retry.log"
                ),
                env=env,
            ),
        ]
