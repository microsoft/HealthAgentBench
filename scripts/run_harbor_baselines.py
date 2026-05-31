from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_TASK_NAME = "ehr_to_meds_etl"
DEFAULT_TASK_PATH = Path("tasks")
DEFAULT_BASELINES_MD = Path("paper/baselines.md")
DEFAULT_HARNESS = "copilot-cli"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_ATTEMPTS = 3
RUN_DIR_SEPARATOR = "__"
RUN_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


@dataclass(frozen=True)
class HarnessSpec:
    name: str
    agent_import_path: str
    display_name: str
    default_models: tuple[str, ...]
    default_agent_kwargs: dict[str, str]


@dataclass(frozen=True)
class ExperimentConfig:
    task_name: str
    task_path: Path
    harness: str
    reasoning_effort: str
    attempts: int
    output_root: Path
    baselines_md: Path
    title: str
    notes: tuple[str, ...]
    mode: str
    run_dirs: tuple[Path, ...]
    models: tuple[str, ...]
    artifacts: tuple[str, ...]
    force_build: bool
    keep_environment: bool
    disable_web_browser: bool = True


@dataclass(frozen=True)
class ModelJobSpec:
    task_name: str
    harness: str
    model_name: str
    reasoning_effort: str
    attempts: int
    run_dir: Path
    launcher_log: Path


@dataclass(frozen=True)
class AttemptResult:
    task_name: str
    harness: str
    model_name: str
    reasoning_effort: str
    attempt: int
    reward: float
    passed: bool
    exception_type: str
    total_wall_time_sec: float | None
    input_tokens: int | None
    cached_tokens: int | None
    output_tokens: int | None
    job_name: str
    run_dir: str
    trial_dir: str


HARNESS_SPECS: dict[str, HarnessSpec] = {
    "copilot-cli": HarnessSpec(
        name="copilot-cli",
        agent_import_path="medcli.agents.harbor.installed.copilot_cli:CopilotCli",
        display_name="GitHub Copilot CLI",
        default_models=(
            "gpt-5.4",
            "gpt-5.4-mini",
            "claude-opus-4.6",
            "claude-sonnet-4.6",
            "claude-haiku-4.5",
        ),
        default_agent_kwargs={},
    ),
    "codex": HarnessSpec(
        name="codex",
        agent_import_path="medcli.agents.harbor.installed.codex:Codex",
        display_name="Codex",
        default_models=("gpt-5.4", "gpt-5.4-mini"),
        default_agent_kwargs={},
    ),
    "claude-code": HarnessSpec(
        name="claude-code",
        agent_import_path="medcli.agents.harbor.installed.claude_code:ClaudeCode",
        display_name="Claude Code",
        default_models=("claude-opus-4-7", "claude-sonnet-4-6"),
        default_agent_kwargs={},
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-name", default=DEFAULT_TASK_NAME)
    parser.add_argument("--task-path", type=Path, default=DEFAULT_TASK_PATH)
    parser.add_argument(
        "--harness", default=DEFAULT_HARNESS, choices=sorted(HARNESS_SPECS)
    )
    parser.add_argument(
        "--model",
        dest="models",
        action="append",
        default=None,
        help="Model name for the selected harness. Can be used multiple times.",
    )
    parser.add_argument("--reasoning-effort", default=DEFAULT_REASONING_EFFORT)
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    parser.add_argument(
        "--mode",
        choices=("run", "render"),
        default="run",
        help="Run Harbor jobs and render markdown, or render from existing run dirs.",
    )
    parser.add_argument(
        "--run-dir",
        dest="run_dirs",
        action="append",
        default=None,
        type=Path,
        help="Existing Harbor run directory to include when --mode=render. Can be used multiple times.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Directory where Harbor run dirs and launcher logs are written.",
    )
    parser.add_argument("--baselines-md", type=Path, default=DEFAULT_BASELINES_MD)
    parser.add_argument(
        "--title",
        default="# Baselines",
        help="Markdown title to use for the generated report.",
    )
    parser.add_argument(
        "--notes",
        action="append",
        default=None,
        help="Optional note line to include in the markdown header. Can be used multiple times.",
    )
    parser.add_argument(
        "--artifact",
        dest="artifacts",
        action="append",
        default=None,
        help="Environment path to download as a Harbor artifact. Can be used multiple times.",
    )
    parser.add_argument(
        "--force-build",
        action="store_true",
        help="Force Harbor to rebuild the Docker environment for each model job.",
    )
    parser.add_argument(
        "--keep-environment",
        action="store_true",
        help="Keep Harbor environments after completion.",
    )
    parser.add_argument(
        "--disable-web-browser",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Disable the agent's built-in web-search / web-fetch tools so it "
            "can't look up gold answers on the public internet. Default: "
            "True. Pass --no-disable-web-browser to re-enable web tools "
            "(use only when you explicitly need the agent to browse). "
            "Translates to harness-specific kwargs: for codex it adds "
            '``-c web_search=\"disabled\"``; for claude-code it adds '
            "``--disallowedTools WebSearch WebFetch``."
        ),
    )
    return parser.parse_args()


def get_harness_spec(name: str) -> HarnessSpec:
    try:
        return HARNESS_SPECS[name]
    except KeyError as exc:
        raise SystemExit(
            f"Unsupported harness {name!r}. Supported harnesses: {', '.join(sorted(HARNESS_SPECS))}."
        ) from exc


def require_copilot_auth() -> None:
    for env_var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        if os.getenv(env_var):
            return

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return

    raise SystemExit(
        "GitHub Copilot auth is required. Set COPILOT_GITHUB_TOKEN, GH_TOKEN, or "
        "GITHUB_TOKEN, or ensure `gh auth token` succeeds."
    )


def require_codex_auth() -> None:
    auth_file = os.environ.get("CODEX_AUTH_FILE", "").strip()
    path = (
        Path(auth_file).expanduser()
        if auth_file
        else Path.home() / ".codex" / "auth.json"
    )
    if path.is_file():
        return

    # Azure path: a config.toml whose providers reference at least one env var set on the host.
    try:
        from medcli.agents.harbor.installed.codex import (
            collect_env_keys_from_config,
            resolve_codex_config,
        )

        config_path = resolve_codex_config()
        if collect_env_keys_from_config(config_path):
            return
    except ValueError:
        pass

    raise SystemExit(
        "Codex auth is required. Expected ~/.codex/auth.json (override via CODEX_AUTH_FILE) "
        "or a ~/.codex/config.toml (override via CODEX_CONFIG_FILE) whose providers "
        "reference at least one env var set on the host."
    )


def require_claude_code_auth() -> None:
    """Accept any of: CLAUDE_CODE_OAUTH_TOKEN, ANTHROPIC_API_KEY,
    ANTHROPIC_AUTH_TOKEN, Bedrock mode, or a readable credentials JSON
    (default ``~/.claude/.credentials.json``, override with
    ``CLAUDE_CODE_AUTH_FILE``).
    """
    if any(
        os.environ.get(k, "").strip()
        for k in (
            "CLAUDE_CODE_OAUTH_TOKEN",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
        )
    ):
        return
    if (
        os.environ.get("CLAUDE_CODE_USE_BEDROCK", "").strip() == "1"
        or os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
    ):
        return
    auth_file = os.environ.get("CLAUDE_CODE_AUTH_FILE", "").strip()
    path = (
        Path(auth_file).expanduser()
        if auth_file
        else Path.home() / ".claude" / ".credentials.json"
    )
    if path.is_file():
        # Pre-load the OAuth token into os.environ so the harbor child
        # processes (spawned from this launcher) inherit it. Harbor's
        # ClaudeCode reads CLAUDE_CODE_OAUTH_TOKEN at run time.
        try:
            payload = json.loads(path.read_text())
            token = (payload.get("claudeAiOauth") or {}).get("accessToken")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            raise SystemExit(
                f"Failed to parse Claude Code credentials at {path}: {exc}"
            ) from exc
        if not token:
            raise SystemExit(
                f"No claudeAiOauth.accessToken in {path}. Re-run `claude login`."
            )
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = token
        return
    raise SystemExit(
        "Claude Code auth is required. Set CLAUDE_CODE_OAUTH_TOKEN or "
        "ANTHROPIC_API_KEY, or ensure ~/.claude/.credentials.json exists "
        "(override path with CLAUDE_CODE_AUTH_FILE)."
    )


def require_harness_auth(harness: str) -> None:
    if harness == "copilot-cli":
        require_copilot_auth()
    elif harness == "codex":
        require_codex_auth()
    elif harness == "claude-code":
        require_claude_code_auth()


def make_timestamp() -> str:
    return datetime.now(UTC).strftime(RUN_TIMESTAMP_FORMAT)


def build_job_name(
    task_name: str, harness: str, model_name: str, timestamp: str
) -> str:
    safe_model = model_name.replace("/", "-")
    return RUN_DIR_SEPARATOR.join((task_name, harness, safe_model, timestamp))


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compute_duration_seconds(
    started_at: str | None, finished_at: str | None
) -> float | None:
    start = parse_iso8601(started_at)
    finish = parse_iso8601(finished_at)
    if start is None or finish is None:
        return None
    return (finish - start).total_seconds()


def default_output_root(repo_root: Path, task_name: str) -> Path:
    return repo_root / "results" / "baselines" / task_name


def build_job_config(
    repo_root: Path,
    experiment: ExperimentConfig,
    harness_spec: HarnessSpec,
    model_name: str,
) -> dict:
    agent_kwargs = dict(harness_spec.default_agent_kwargs)
    if experiment.reasoning_effort:
        agent_kwargs["reasoning_effort"] = experiment.reasoning_effort

    # Optionally disable the agent's built-in web-search / web-fetch tools so
    # it can't look up gold answers on the public internet. Each harness has
    # a different CLI surface — translate here:
    #   * codex:        ``disable_web_search=True`` → ``-c web_search="disabled"``
    #     (extension defined in src/medcli/agents/harbor/installed/codex.py)
    #   * claude-code:  ``disallowed_tools="WebSearch WebFetch"`` →
    #     ``--disallowedTools WebSearch WebFetch`` (upstream Harbor flag)
    #   * copilot-cli:  no public web-browsing toggle in the upstream agent;
    #     skip silently rather than fail loud.
    if experiment.disable_web_browser:
        if harness_spec.name == "codex":
            agent_kwargs.setdefault("disable_web_search", True)
        elif harness_spec.name == "claude-code":
            agent_kwargs.setdefault("disallowed_tools", "WebSearch WebFetch")

    task_path = experiment.task_path
    if not task_path.is_absolute():
        task_path = (repo_root / task_path).resolve()

    return {
        "n_attempts": experiment.attempts,
        "timeout_multiplier": 1.0,
        "n_concurrent_trials": 1,
        "quiet": False,
        "environment": {
            "type": "docker",
            "force_build": experiment.force_build,
            "delete": not experiment.keep_environment,
        },
        "agents": [
            {
                "import_path": harness_spec.agent_import_path,
                "model_name": model_name,
                "kwargs": agent_kwargs,
            }
        ],
        "datasets": [{"path": str(task_path), "task_names": [experiment.task_name]}],
        "artifacts": list(experiment.artifacts),
    }


def emit_prefixed_output(prefix: str, stream, sink) -> None:
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            sink.write(line)
            sink.flush()
            sys.stdout.write(f"[{prefix}] {line}")
            sys.stdout.flush()
    finally:
        stream.close()


def launch_model_job(
    repo_root: Path,
    experiment: ExperimentConfig,
    harness_spec: HarnessSpec,
    spec: ModelJobSpec,
) -> int:
    spec.run_dir.parent.mkdir(parents=True, exist_ok=True)
    spec.launcher_log.parent.mkdir(parents=True, exist_ok=True)

    job_config = build_job_config(repo_root, experiment, harness_spec, spec.model_name)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix=f"{spec.model_name.replace('/', '_')}_",
        delete=False,
    ) as handle:
        json.dump(job_config, handle, indent=2)
        handle.write("\n")
        config_path = Path(handle.name)

    command = [
        "uv",
        "run",
        "harbor",
        "run",
        "-c",
        str(config_path),
        "--job-name",
        spec.run_dir.name,
        "--jobs-dir",
        str(spec.run_dir.parent),
    ]

    with spec.launcher_log.open("w", encoding="utf-8") as sink:
        sink.write(f"Command: {' '.join(command)}\n")
        sink.flush()
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        reader = threading.Thread(
            target=emit_prefixed_output,
            args=(f"{spec.harness}:{spec.model_name}", process.stdout, sink),
            daemon=True,
        )
        reader.start()
        return_code = process.wait()
        reader.join()
        sink.write(f"\nExit code: {return_code}\n")

    try:
        config_path.unlink()
    except FileNotFoundError:
        pass

    return return_code


def load_job_config_metadata(run_dir: Path) -> dict:
    config_path = run_dir / "config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def infer_run_metadata_from_name(
    run_dir: Path, fallback_task_name: str = ""
) -> dict[str, str]:
    parts = run_dir.name.split(RUN_DIR_SEPARATOR)
    if len(parts) < 4:
        legacy_name = run_dir.name
        for harness_name in sorted(HARNESS_SPECS, key=len, reverse=True):
            prefix = f"{harness_name}_"
            if not legacy_name.startswith(prefix):
                continue
            tail = legacy_name.removeprefix(prefix)
            if "_" not in tail:
                continue
            model_name, timestamp = tail.rsplit("_", 1)
            return {
                "task_name": fallback_task_name,
                "harness": harness_name,
                "model_name": model_name,
                "timestamp": timestamp,
            }
        return {}
    return {
        "task_name": parts[0],
        "harness": parts[1],
        "model_name": RUN_DIR_SEPARATOR.join(parts[2:-1]),
        "timestamp": parts[-1],
    }


def infer_run_metadata(
    run_dir: Path,
    default_reasoning_effort: str,
    fallback_task_name: str = "",
) -> tuple[str, str, str, str]:
    config = load_job_config_metadata(run_dir)
    datasets = config.get("datasets") or []
    agents = config.get("agents") or []

    task_name = ""
    if datasets and isinstance(datasets[0], dict):
        task_names = datasets[0].get("task_names") or []
        if task_names:
            task_name = task_names[0]

    harness = ""
    model_name = ""
    reasoning_effort = default_reasoning_effort
    if agents and isinstance(agents[0], dict):
        agent = agents[0]
        model_name = agent.get("model_name") or ""
        kwargs = agent.get("kwargs") or {}
        reasoning_effort = kwargs.get("reasoning_effort") or default_reasoning_effort
        import_path = agent.get("import_path") or ""
        for spec in HARNESS_SPECS.values():
            if spec.agent_import_path == import_path:
                harness = spec.name
                break

    if not task_name or not harness or not model_name:
        fallback = infer_run_metadata_from_name(
            run_dir, fallback_task_name=fallback_task_name
        )
        task_name = task_name or fallback.get("task_name", "")
        harness = harness or fallback.get("harness", "")
        model_name = model_name or fallback.get("model_name", "")

    if not task_name or not harness or not model_name:
        raise SystemExit(f"Unable to infer task/harness/model from run dir: {run_dir}")

    return task_name, harness, model_name, reasoning_effort


def make_missing_attempt(
    *,
    task_name: str,
    harness: str,
    model_name: str,
    reasoning_effort: str,
    attempt: int,
    job_name: str,
    run_dir: Path,
    exception_type: str,
) -> AttemptResult:
    return AttemptResult(
        task_name=task_name,
        harness=harness,
        model_name=model_name,
        reasoning_effort=reasoning_effort,
        attempt=attempt,
        reward=0.0,
        passed=False,
        exception_type=exception_type,
        total_wall_time_sec=None,
        input_tokens=None,
        cached_tokens=None,
        output_tokens=None,
        job_name=job_name,
        run_dir=str(run_dir),
        trial_dir="",
    )


def load_attempt_results_for_run_dir(
    *,
    task_name: str,
    harness: str,
    model_name: str,
    reasoning_effort: str,
    run_dir: Path,
    attempts: int,
) -> list[AttemptResult]:
    if not run_dir.exists():
        return [
            make_missing_attempt(
                task_name=task_name,
                harness=harness,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                attempt=index,
                job_name=run_dir.name,
                run_dir=run_dir,
                exception_type="LaunchError",
            )
            for index in range(1, attempts + 1)
        ]

    trial_result_paths = sorted(run_dir.glob(f"{task_name}__*/result.json"))
    if not trial_result_paths:
        return [
            make_missing_attempt(
                task_name=task_name,
                harness=harness,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                attempt=index,
                job_name=run_dir.name,
                run_dir=run_dir,
                exception_type="LaunchError",
            )
            for index in range(1, attempts + 1)
        ]

    sorted_payloads: list[tuple[datetime, dict, Path]] = []
    for path in trial_result_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        timestamp = parse_iso8601(payload.get("started_at")) or datetime.min.replace(
            tzinfo=UTC
        )
        sorted_payloads.append((timestamp, payload, path))
    sorted_payloads.sort(key=lambda item: item[0])

    parsed_attempts: list[AttemptResult] = []
    for index, (_, payload, path) in enumerate(sorted_payloads, start=1):
        reward = payload.get("verifier_result", {}).get("rewards", {}).get("reward")
        reward_value = float(reward) if reward is not None else 0.0
        parsed_attempts.append(
            AttemptResult(
                task_name=task_name,
                harness=harness,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                attempt=index,
                reward=reward_value,
                passed=reward_value == 1.0,
                exception_type=(payload.get("exception_info") or {}).get(
                    "exception_type", ""
                ),
                total_wall_time_sec=compute_duration_seconds(
                    payload.get("started_at"),
                    payload.get("finished_at"),
                ),
                input_tokens=(payload.get("agent_result") or {}).get("n_input_tokens"),
                cached_tokens=(payload.get("agent_result") or {}).get("n_cache_tokens"),
                output_tokens=(payload.get("agent_result") or {}).get(
                    "n_output_tokens"
                ),
                job_name=run_dir.name,
                run_dir=str(run_dir),
                trial_dir=str(path.parent),
            )
        )

    while len(parsed_attempts) < attempts:
        parsed_attempts.append(
            make_missing_attempt(
                task_name=task_name,
                harness=harness,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                attempt=len(parsed_attempts) + 1,
                job_name=run_dir.name,
                run_dir=run_dir,
                exception_type="MissingTrialResult",
            )
        )

    return parsed_attempts[:attempts]


def format_float(value: float | None, digits: int = 2) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def format_int(value: int | None) -> str:
    if value is None:
        return ""
    return str(value)


def markdown_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "_No rows recorded._"

    headers = list(rows[0].keys())
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    body_lines = [
        "| " + " | ".join(str(row[header]) for header in headers) + " |" for row in rows
    ]
    return "\n".join([header_line, separator_line, *body_lines])


def build_document_intro(title: str) -> str:
    lines = [
        title,
        "",
        "Harbor baseline runs across tasks and installed-agent harnesses, generated with "
        "[`scripts/run_harbor_baselines.py`](../scripts/run_harbor_baselines.py).",
        "",
        "",
    ]
    return "\n".join(lines)


def extract_task_section_headers(markdown: str) -> list[str]:
    subsection_headers = {
        "## Aggregate Summary",
        "## Detailed Attempts",
        "## Reproducibility",
    }
    return [
        line
        for line in markdown.splitlines()
        if line.startswith("## ") and line not in subsection_headers
    ]


def build_repro_command(experiment: ExperimentConfig, output_root: Path) -> list[str]:
    command = [
        "uv run python scripts/run_harbor_baselines.py \\",
        f"  --task-name {experiment.task_name} \\",
        f"  --task-path {experiment.task_path} \\",
        f"  --harness {experiment.harness} \\",
        f"  --output-root {output_root} \\",
        f"  --attempts {experiment.attempts} \\",
        f"  --reasoning-effort {experiment.reasoning_effort}",
    ]
    for model_name in experiment.models:
        command[-1] += " \\"
        command.append(f"  --model {model_name}")
    return command


def build_task_section(
    experiment: ExperimentConfig,
    run_timestamp: str,
    output_root: Path,
    all_attempts: list[AttemptResult],
) -> str:
    grouped: dict[tuple[str, str, str, str], list[AttemptResult]] = {}
    for item in all_attempts:
        grouped.setdefault(
            (item.task_name, item.harness, item.model_name, item.reasoning_effort),
            [],
        ).append(item)

    grouped_stats: list[
        tuple[
            tuple[str, str, str, str],
            list[AttemptResult],
            float,
            float,
            int,
            float | None,
        ]
    ] = []
    for key in sorted(grouped):
        attempts = sorted(grouped[key], key=lambda item: item.attempt)
        rewards = [item.reward for item in attempts]
        wall_times = [
            item.total_wall_time_sec
            for item in attempts
            if item.total_wall_time_sec is not None
        ]
        mean_reward = statistics.mean(rewards)
        reward_variance = statistics.pvariance(rewards)
        successes = sum(1 for item in attempts if item.passed)
        mean_wall_time = statistics.mean(wall_times) if wall_times else None
        grouped_stats.append(
            (key, attempts, mean_reward, reward_variance, successes, mean_wall_time)
        )

    grouped_stats.sort(
        key=lambda item: (
            -item[2],
            -item[4],
            item[3],
            item[0][0],
            item[0][1],
            item[0][2],
            item[0][3],
        )
    )

    aggregate_rows = []
    for (
        key,
        attempts,
        mean_reward,
        reward_variance,
        successes,
        mean_wall_time,
    ) in grouped_stats:
        aggregate_rows.append(
            {
                "Task": key[0],
                "Harness": key[1],
                "Model": key[2],
                "Reasoning": key[3],
                "Runs": str(len(attempts)),
                "Mean reward": format_float(mean_reward, 3),
                "Reward variance": format_float(reward_variance, 3),
                "Successes": str(successes),
                "Mean total wall time (s)": format_float(mean_wall_time, 2),
            }
        )

    detailed_rows = []
    for _, attempts, _, _, _, _ in grouped_stats:
        for item in attempts:
            detailed_rows.append(
                {
                    "Task": item.task_name,
                    "Harness": item.harness,
                    "Model": item.model_name,
                    "Reasoning": item.reasoning_effort,
                    "Attempt": str(item.attempt),
                    "Reward": format_float(item.reward, 3),
                    "Passed": "Yes" if item.passed else "No",
                    "Exception type": item.exception_type,
                    "Total wall time (s)": format_float(item.total_wall_time_sec, 2),
                    "Input tokens": format_int(item.input_tokens),
                    "Cached tokens": format_int(item.cached_tokens),
                    "Output tokens": format_int(item.output_tokens),
                    "Run dir": f"`{item.run_dir}`" if item.run_dir else "",
                    "Trial dir": f"`{item.trial_dir}`" if item.trial_dir else "",
                }
            )

    lines = [
        f"## {experiment.task_name}",
        "",
        f"- Task path: `{experiment.task_path}`",
        f"- Generated at: `{run_timestamp}`",
        f"- Raw results root: `{output_root}`",
    ]
    for note in experiment.notes:
        lines.append(f"- Note: {note}")

    lines.extend(
        [
            "",
            "### Aggregate Summary",
            "",
            markdown_table(aggregate_rows),
            "",
            "### Detailed Attempts",
            "",
            markdown_table(detailed_rows),
            "",
            "### Reproducibility",
            "",
            "```bash",
            *build_repro_command(experiment, output_root),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def upsert_task_section(
    existing_text: str, task_name: str, task_section: str, title: str
) -> str:
    document = existing_text.strip()
    if not document:
        return build_document_intro(title) + task_section.strip() + "\n"

    if not extract_task_section_headers(document):
        return build_document_intro(title) + task_section.strip() + "\n"

    section_header = f"## {task_name}\n"
    start = document.find(section_header)
    if start == -1:
        return document + "\n\n" + task_section.strip() + "\n"

    next_section = document.find("\n## ", start + len(section_header))
    if next_section == -1:
        return document[:start].rstrip() + "\n\n" + task_section.strip() + "\n"

    prefix = document[:start].rstrip()
    suffix = document[next_section:].lstrip("\n")
    return prefix + "\n\n" + task_section.strip() + "\n\n" + suffix


def write_baselines_markdown(
    baselines_md: Path,
    *,
    task_name: str,
    task_section: str,
    title: str,
) -> None:
    baselines_md.parent.mkdir(parents=True, exist_ok=True)
    existing_text = ""
    if baselines_md.exists():
        existing_text = baselines_md.read_text(encoding="utf-8")

    baselines_md.write_text(
        upsert_task_section(existing_text, task_name, task_section, title),
        encoding="utf-8",
    )


def build_experiment_config(
    args: argparse.Namespace, repo_root: Path
) -> ExperimentConfig:
    harness_spec = get_harness_spec(args.harness)
    models = tuple(args.models or harness_spec.default_models)
    output_root = args.output_root or default_output_root(repo_root, args.task_name)
    return ExperimentConfig(
        task_name=args.task_name,
        task_path=args.task_path,
        harness=args.harness,
        reasoning_effort=args.reasoning_effort,
        attempts=args.attempts,
        output_root=output_root,
        baselines_md=args.baselines_md,
        title=args.title,
        notes=tuple(args.notes or ()),
        mode=args.mode,
        run_dirs=tuple(args.run_dirs or ()),
        models=models,
        artifacts=tuple(args.artifacts or ()),
        force_build=args.force_build,
        keep_environment=args.keep_environment,
        disable_web_browser=args.disable_web_browser,
    )


def render_from_run_dirs(experiment: ExperimentConfig) -> None:
    all_attempts: list[AttemptResult] = []
    seen_tasks: set[str] = set()
    seen_harnesses: set[str] = set()
    seen_models: set[str] = set()

    for run_dir in experiment.run_dirs:
        task_name, harness, model_name, reasoning_effort = infer_run_metadata(
            run_dir,
            experiment.reasoning_effort,
            fallback_task_name=experiment.task_name,
        )
        seen_tasks.add(task_name)
        seen_harnesses.add(harness)
        seen_models.add(model_name)
        all_attempts.extend(
            load_attempt_results_for_run_dir(
                task_name=task_name,
                harness=harness,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                run_dir=run_dir,
                attempts=experiment.attempts,
            )
        )

    report_experiment = experiment
    if len(seen_tasks) == 1 and len(seen_harnesses) == 1:
        report_experiment = ExperimentConfig(
            task_name=next(iter(seen_tasks)),
            task_path=experiment.task_path,
            harness=next(iter(seen_harnesses)),
            reasoning_effort=experiment.reasoning_effort,
            attempts=experiment.attempts,
            output_root=experiment.output_root,
            baselines_md=experiment.baselines_md,
            title=experiment.title,
            notes=experiment.notes,
            mode=experiment.mode,
            run_dirs=experiment.run_dirs,
            models=tuple(sorted(seen_models)),
            artifacts=experiment.artifacts,
            force_build=experiment.force_build,
            keep_environment=experiment.keep_environment,
        )

    write_baselines_markdown(
        experiment.baselines_md,
        task_name=report_experiment.task_name,
        task_section=build_task_section(
            report_experiment,
            make_timestamp(),
            experiment.output_root,
            all_attempts,
        ),
        title=experiment.title,
    )
    print(f"Wrote baseline summary to {experiment.baselines_md}")


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    experiment = build_experiment_config(args, repo_root)
    harness_spec = get_harness_spec(experiment.harness)

    if experiment.mode == "render":
        if not experiment.run_dirs:
            raise SystemExit("--mode=render requires at least one --run-dir.")
        render_from_run_dirs(experiment)
        return

    require_harness_auth(experiment.harness)
    experiment.output_root.mkdir(parents=True, exist_ok=True)

    timestamp = make_timestamp()
    specs = [
        ModelJobSpec(
            task_name=experiment.task_name,
            harness=experiment.harness,
            model_name=model_name,
            reasoning_effort=experiment.reasoning_effort,
            attempts=experiment.attempts,
            run_dir=experiment.output_root
            / build_job_name(
                experiment.task_name, experiment.harness, model_name, timestamp
            ),
            launcher_log=experiment.output_root
            / (
                build_job_name(
                    experiment.task_name, experiment.harness, model_name, timestamp
                )
                + ".launcher.log"
            ),
        )
        for model_name in experiment.models
    ]

    processes: list[tuple[ModelJobSpec, threading.Thread, dict[str, int]]] = []
    for spec in specs:
        holder: dict[str, int] = {}
        thread = threading.Thread(
            target=lambda result_holder, job_spec: result_holder.setdefault(
                "returncode",
                launch_model_job(repo_root, experiment, harness_spec, job_spec),
            ),
            args=(holder, spec),
            daemon=False,
        )
        thread.start()
        processes.append((spec, thread, holder))

    for _, thread, _ in processes:
        thread.join()

    all_attempts: list[AttemptResult] = []
    for spec, _, holder in processes:
        return_code = holder.get("returncode", 1)
        if return_code != 0:
            print(
                f"[{spec.harness}:{spec.model_name}] harbor exited with code {return_code}"
            )
        all_attempts.extend(
            load_attempt_results_for_run_dir(
                task_name=spec.task_name,
                harness=spec.harness,
                model_name=spec.model_name,
                reasoning_effort=spec.reasoning_effort,
                run_dir=spec.run_dir,
                attempts=spec.attempts,
            )
        )

    write_baselines_markdown(
        experiment.baselines_md,
        task_name=experiment.task_name,
        task_section=build_task_section(
            experiment,
            timestamp,
            experiment.output_root,
            all_attempts,
        ),
        title=experiment.title,
    )

    print(f"Wrote baseline summary to {experiment.baselines_md}")
    for spec in specs:
        print(f"- {spec.harness}:{spec.model_name}: {spec.run_dir}")


if __name__ == "__main__":
    main()
