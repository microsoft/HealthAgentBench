import os
import shlex
import tomllib
from pathlib import Path

from harbor.agents.installed.base import CliFlag, with_prompt_template
from harbor.agents.installed.codex import Codex as HarborCodex
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths


def resolve_codex_config() -> Path:
    """Return the path to the host's Codex config TOML.

    Honors ``CODEX_CONFIG_FILE`` if set; otherwise falls back to
    ``~/.codex/config.toml``. Raises ``ValueError`` if the file is missing.
    """
    override = os.environ.get("CODEX_CONFIG_FILE", "").strip()
    path = (
        Path(override).expanduser()
        if override
        else Path.home() / ".codex" / "config.toml"
    )
    if not path.is_file():
        raise ValueError(
            f"Codex config file not found at {path}. "
            "Expected ~/.codex/config.toml or set CODEX_CONFIG_FILE."
        )
    return path


def collect_env_keys_from_config(config_path: Path) -> dict[str, str]:
    """Walk ``[model_providers.*]`` tables and resolve each ``env_key`` from the host.

    Returns a ``{env_name: value}`` dict containing only the keys that resolve to
    a non-empty value on the host. Providers without an ``env_key`` are skipped,
    as are providers whose key is unset on the host (so users can keep unused
    providers configured without forcing every region's key to be present).
    """
    try:
        with config_path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(
            f"Failed to parse Codex config at {config_path}: {exc}"
        ) from exc

    resolved: dict[str, str] = {}
    providers = data.get("model_providers") or {}
    if not isinstance(providers, dict):
        return resolved
    for provider in providers.values():
        if not isinstance(provider, dict):
            continue
        env_key = provider.get("env_key")
        if not env_key or not isinstance(env_key, str):
            continue
        value = os.environ.get(env_key, "").strip()
        if value:
            resolved[env_key] = value
    return resolved


class Codex(HarborCodex):
    """MedCLI wrapper around Harbor's Codex installed agent."""

    # Extend the upstream CLI flag list with a ``disable_web_search`` toggle.
    # When True (the default for MedCLI sweeps), we pass
    # ``-c web_search="disabled"`` so the Codex CLI's built-in web-search
    # tool is unavailable to the agent for the duration of the trial. This
    # prevents the agent from looking up gold reports on the public internet
    # — see the gpt-5.3-codex web_search leak observed on xray_report_correction
    # for context.
    #
    # The Codex config key is the top-level ``web_search`` (string-valued:
    # ``"disabled" | "cached" | "live"``). An earlier version of this flag
    # used ``-c tools.web_search=false``, which the Codex CLI silently
    # ignored — the agent kept emitting real ``action.type=search`` calls
    # and cheating on xray_report_correction. See
    # https://developers.openai.com/codex/config-reference for the
    # canonical key + allowed values.
    CLI_FLAGS = [
        *HarborCodex.CLI_FLAGS,
        CliFlag(
            "disable_web_search",
            # When ``disable_web_search=True``, Harbor's bool handling
            # (see harbor.agents.installed.base.build_cli_flags) appends
            # this entire string to the command as a single token. When
            # False/unset, nothing is appended.
            cli='-c web_search="disabled"',
            type="bool",
        ),
    ]

    @staticmethod
    def _resolve_auth_file() -> Path:
        auth_file = os.environ.get("CODEX_AUTH_FILE", "").strip()
        path = (
            Path(auth_file).expanduser()
            if auth_file
            else Path.home() / ".codex" / "auth.json"
        )
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

        else:
            config_path = resolve_codex_config()
            azure_env = collect_env_keys_from_config(config_path)
            if not azure_env:
                raise ValueError(
                    "No Codex credentials found. Set CODEX_AUTH_JSON, or configure "
                    "providers in ~/.codex/config.toml and export at least one env "
                    "var referenced by `env_key` (override path via CODEX_CONFIG_FILE)."
                )
            await self.exec_as_agent(environment, command="mkdir -p /tmp/codex-secrets")
            await environment.upload_file(
                source_path=config_path,
                target_path="/tmp/codex-secrets/config.toml",
            )
            env.update(azure_env)
            setup_command = """
mkdir -p "$CODEX_HOME"
ln -sf /tmp/codex-secrets/config.toml "$CODEX_HOME/config.toml"
"""

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
                    'trap \'rm -rf /tmp/codex-secrets "$CODEX_HOME/auth.json" "$CODEX_HOME/config.toml"\' EXIT TERM INT; '
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
                    command='rm -rf /tmp/codex-secrets "$CODEX_HOME/auth.json" "$CODEX_HOME/config.toml"',
                    env={"CODEX_HOME": EnvironmentPaths.agent_dir.as_posix()},
                )
            except Exception:
                pass
