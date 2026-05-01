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


DEFAULT_TASK_NAME = "mimic_iv_meds"
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
    include_detailed: bool = True
    metrics_script: Path | None = None
    concurrency: int = 1
    subtasks: tuple[str, ...] = ()
    metric_to_report: tuple[str, ...] = ()


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
    fill_rate: float | None
    exception_type: str
    total_wall_time_sec: float | None
    input_tokens: int | None
    cached_tokens: int | None
    output_tokens: int | None
    job_name: str
    run_dir: str
    trial_dir: str
    # Harbor's per-trial `task_name` (the concrete subtask, e.g.
    # `p10046166_s50051329`) — distinct from `task_name` above which is the
    # launcher-level parent label. Used to count unique subtasks per run.
    subtask_name: str = ""
    # Full per-trial rewards dict (everything the verifier emitted into
    # `verifier/reward.json`). Used to compute mean+stdev across trials for
    # arbitrary --metric-to-report keys that are per-trial scalars.
    rewards_raw: tuple[tuple[str, float | int], ...] = ()


def _load_run_dir_metric(run_dir: Path) -> dict:
    """Return the uv-script aggregator's output for this Harbor run.

    Harbor stores the output of any `metrics: [{type: uv-script, ...}]` entry
    inside the job's `result.json` at `stats.evals.<evals_key>.metrics[0]`.
    If multiple evals_keys exist (e.g. when task_name doesn't match exactly
    and we fall back), we pick the first non-empty metric dict we find.
    Returns {} when Harbor hasn't written metrics yet or the structure differs.
    """
    result_path = run_dir / "result.json"
    if not result_path.exists():
        return {}
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    evals = (data.get("stats") or {}).get("evals") or {}
    for _, eval_payload in evals.items():
        metrics = eval_payload.get("metrics") or []
        if metrics and isinstance(metrics[0], dict) and metrics[0]:
            return metrics[0]
    return {}


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
    parser.add_argument("--harness", default=DEFAULT_HARNESS, choices=sorted(HARNESS_SPECS))
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
        "--no-detailed",
        dest="include_detailed",
        action="store_false",
        default=True,
        help="Skip the 'Detailed Attempts' subsection in the generated markdown.",
    )
    parser.add_argument(
        "--metrics-script",
        type=Path,
        default=None,
        help=(
            "PEP 723 uv-script that Harbor invokes after all trials complete to "
            "aggregate pooled metrics (e.g. scripts/mimic_report_gen/"
            "aggregate_metric.py for CheXbert F1). If omitted, the launcher looks "
            "for scripts/<task_name>/aggregate_metric.py and a few slug variants."
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Harbor n_concurrent_trials. Bump this for multi-patient sweeps.",
    )
    parser.add_argument(
        "--subtask",
        dest="subtasks",
        action="append",
        default=None,
        help=(
            "Restrict execution to specific subtask names under the parent task "
            "dir (e.g. 'p10046166_s50051329'). Repeat --subtask to pick multiple. "
            "Useful for debugging one or a few patients. When omitted, ALL "
            "subtasks under the parent dir are run."
        ),
    )
    parser.add_argument(
        "--metric-to-report",
        dest="metric_to_report",
        action="append",
        default=None,
        help=(
            "Flat key from the uv-script aggregator's output to add as a "
            "column in the baselines.md Aggregate Summary table "
            "(e.g. 'chexbert_f1_14_macro_f1'). Repeat --metric-to-report "
            "to add more than one. Each key is looked up verbatim in the "
            "aggregated metric dict stored at "
            "`<run_dir>/result.json → stats.evals.<evals_key>.metrics[0]`."
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
    path = Path(auth_file).expanduser() if auth_file else Path.home() / ".codex" / "auth.json"
    if path.is_file():
        return
    raise SystemExit(
        "Codex auth is required. Expected ~/.codex/auth.json or set CODEX_AUTH_FILE."
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


def build_job_name(task_name: str, harness: str, model_name: str, timestamp: str) -> str:
    safe_model = model_name.replace("/", "-")
    return RUN_DIR_SEPARATOR.join((task_name, harness, safe_model, timestamp))


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compute_duration_seconds(started_at: str | None, finished_at: str | None) -> float | None:
    start = parse_iso8601(started_at)
    finish = parse_iso8601(finished_at)
    if start is None or finish is None:
        return None
    return (finish - start).total_seconds()


def default_output_root(repo_root: Path, task_name: str) -> Path:
    return repo_root / "results" / "baselines" / task_name


def _is_parent_task_dir(task_dir: Path) -> bool:
    """A directory is a meta-task parent iff it has no task.toml of its own but
    contains subdirectories that do. We treat such a dir as a *label* for a
    collection of sibling tasks that Harbor should enumerate."""
    if not task_dir.is_dir():
        return False
    if (task_dir / "task.toml").exists():
        return False
    for sub in task_dir.iterdir():
        if sub.is_dir() and (sub / "task.toml").exists():
            return True
    return False


def _autodetect_metrics_script(repo_root: Path, task_name: str) -> Path | None:
    """Return scripts/<slug>/aggregate_metric.py for the first slug that exists.

    Accepts the task name as-is plus common slug variants (_ <-> -) so that a
    task dir named `mimic_report_gen` can still find `scripts/mimic_report_gen/`.
    """
    candidates = {
        task_name,
        task_name.replace("_", "-"),
        task_name.replace("-", "_"),
    }
    # Also try appending "-generation" / "_generation" to catch short forms.
    extras = []
    for c in list(candidates):
        extras.append(c + "-generation")
        extras.append(c + "_generation")
        extras.append(c.replace("-gen", "-generation").replace("_gen", "_generation"))
    candidates.update(extras)
    for slug in sorted(candidates, key=len, reverse=True):
        path = repo_root / "scripts" / slug / "aggregate_metric.py"
        if path.is_file():
            return path
    return None


def build_job_config(
    repo_root: Path,
    experiment: ExperimentConfig,
    harness_spec: HarnessSpec,
    model_name: str,
) -> dict:
    agent_kwargs = dict(harness_spec.default_agent_kwargs)
    if experiment.reasoning_effort:
        agent_kwargs["reasoning_effort"] = experiment.reasoning_effort

    task_path = experiment.task_path
    if not task_path.is_absolute():
        task_path = (repo_root / task_path).resolve()

    # If <task_path>/<task_name>/ is a meta-task parent dir (contains subtask
    # dirs), rewrite the Harbor dataset spec so it enumerates all subtasks.
    candidate_parent = task_path / experiment.task_name
    if _is_parent_task_dir(candidate_parent):
        dataset_path = candidate_parent
        # If the user supplied --subtask filters, only run those patients;
        # otherwise run every subdir via the "*" glob.
        if experiment.subtasks:
            dataset_task_names = list(experiment.subtasks)
        else:
            dataset_task_names = ["*"]
    else:
        dataset_path = task_path
        dataset_task_names = [experiment.task_name]

    config: dict = {
        "n_attempts": experiment.attempts,
        "timeout_multiplier": 1.0,
        "n_concurrent_trials": experiment.concurrency,
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
        "datasets": [{"path": str(dataset_path), "task_names": dataset_task_names}],
        "artifacts": list(experiment.artifacts),
    }

    # Resolve metrics uv-script (explicit flag beats auto-detect).
    metrics_script = experiment.metrics_script
    if metrics_script is None:
        metrics_script = _autodetect_metrics_script(repo_root, experiment.task_name)
    if metrics_script is not None:
        path = metrics_script
        if not path.is_absolute():
            path = (repo_root / path).resolve()
        config["metrics"] = [
            {"type": "uv-script", "kwargs": {"script_path": str(path)}}
        ]

    return config


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


def infer_run_metadata_from_name(run_dir: Path, fallback_task_name: str = "") -> dict[str, str]:
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
            # Harbor expands `task_names: ["*"]` into the explicit subtask list
            # when writing config.json. Detect parent-dir mode by: (a) literal
            # glob, or (b) multiple task names (a single literal task never
            # produces >1 entry). In that case prefer the run-dir name prefix
            # (which holds the user's --task-name) or the explicit fallback.
            if (
                task_names == ["*"]
                or any("*" in n for n in task_names)
                or len(task_names) > 1
            ):
                name_parts = run_dir.name.split(RUN_DIR_SEPARATOR)
                task_name = name_parts[0] if len(name_parts) >= 4 else fallback_task_name
            else:
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
        fallback = infer_run_metadata_from_name(run_dir, fallback_task_name=fallback_task_name)
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
        fill_rate=None,
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

    # Accept any trial dir name: Harbor uses "<trial_task>__<suffix>" regardless
    # of whether the launcher passed a literal task name or expanded a parent dir
    # into many subtasks.
    trial_result_paths = sorted(run_dir.glob("*__*/result.json"))
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
        timestamp = parse_iso8601(payload.get("started_at")) or datetime.min.replace(tzinfo=UTC)
        sorted_payloads.append((timestamp, payload, path))
    sorted_payloads.sort(key=lambda item: item[0])

    parsed_attempts: list[AttemptResult] = []
    for index, (_, payload, path) in enumerate(sorted_payloads, start=1):
        # ``verifier_result`` is None when the trial failed before the verifier
        # ran (e.g. docker compose error). Treat as empty rewards.
        verifier_result = payload.get("verifier_result") or {}
        rewards = verifier_result.get("rewards", {}) or {}
        reward = rewards.get("reward")
        reward_value = float(reward) if reward is not None else 0.0
        fill_rate_raw = rewards.get("fill_rate")
        fill_rate_value = float(fill_rate_raw) if fill_rate_raw is not None else None
        # Augment Harbor's `verifier_result.rewards` (typically only `reward`)
        # with the richer scalars the verifier wrote into
        # `<trial_dir>/verifier/reward.json` (e.g. f1, recall, precision,
        # n_clusters). Harbor's `reward` always wins on key collision so the
        # canonical primary metric stays consistent.
        extra_rewards: dict[str, float | int] = {}
        reward_json_path = path.parent / "verifier" / "reward.json"
        if reward_json_path.exists():
            try:
                rj = json.loads(reward_json_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                rj = {}
            if isinstance(rj, dict):
                for k, v in rj.items():
                    if isinstance(v, (int, float)):
                        extra_rewards[k] = v
        merged_rewards = {**extra_rewards, **rewards}
        rewards_raw_frozen: tuple[tuple[str, float | int], ...] = tuple(
            sorted(
                (k, v)
                for k, v in merged_rewards.items()
                if isinstance(v, (int, float))
            )
        )
        parsed_attempts.append(
            AttemptResult(
                task_name=task_name,
                harness=harness,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                attempt=index,
                reward=reward_value,
                passed=reward_value == 1.0,
                fill_rate=fill_rate_value,
                exception_type=(payload.get("exception_info") or {}).get("exception_type", ""),
                total_wall_time_sec=compute_duration_seconds(
                    payload.get("started_at"),
                    payload.get("finished_at"),
                ),
                input_tokens=(payload.get("agent_result") or {}).get("n_input_tokens"),
                cached_tokens=(payload.get("agent_result") or {}).get("n_cache_tokens"),
                output_tokens=(payload.get("agent_result") or {}).get("n_output_tokens"),
                job_name=run_dir.name,
                run_dir=str(run_dir),
                trial_dir=str(path.parent),
                subtask_name=str(payload.get("task_name") or ""),
                rewards_raw=rewards_raw_frozen,
            )
        )

    # Return every trial Harbor actually ran. We intentionally do NOT pad to
    # `attempts` or trim by it: with multi-subtask benchmarks each subtask
    # contributes its own trial(s), so total trials = subtasks × attempts.
    # Padding would invent fake "MissingTrialResult" rows; trimming would
    # silently drop real ones (which masked a 2-patient run as a single
    # trial and zeroed the Reward stdev).
    return parsed_attempts


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
        "| " + " | ".join(str(row[header]) for header in headers) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator_line, *body_lines])


def _invoked_script_rel() -> str:
    """Return the currently-running script path, relative to the repo root
    when possible. Lets sibling copies like run_harbor_baselines_multitask.py
    render accurate Reproducibility / intro links without forking the code.
    """
    try:
        here = Path(__file__).resolve()
        repo_root = Path(__file__).resolve().parents[1]
        return str(here.relative_to(repo_root))
    except (ValueError, OSError):
        return f"scripts/{Path(__file__).name}"


def build_document_intro(title: str) -> str:
    script_rel = _invoked_script_rel()
    lines = [
        title,
        "",
        "Harbor baseline runs across tasks and installed-agent harnesses, generated with "
        f"[`{script_rel}`](../{script_rel}).",
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
        f"uv run python {_invoked_script_rel()} \\",
        f"  --task-name {experiment.task_name} \\",
        f"  --task-path {experiment.task_path} \\",
        f"  --harness {experiment.harness} \\",
        f"  --output-root {output_root} \\",
        f"  --attempts {experiment.attempts} \\",
        f"  --reasoning-effort {experiment.reasoning_effort}",
    ]
    if experiment.concurrency and experiment.concurrency != 1:
        command[-1] += " \\"
        command.append(f"  --concurrency {experiment.concurrency}")
    if experiment.metrics_script is not None:
        command[-1] += " \\"
        command.append(f"  --metrics-script {experiment.metrics_script}")
    if not experiment.include_detailed:
        command[-1] += " \\"
        command.append("  --no-detailed")
    for sub in experiment.subtasks:
        command[-1] += " \\"
        command.append(f"  --subtask {sub}")
    for m in experiment.metric_to_report:
        command[-1] += " \\"
        command.append(f"  --metric-to-report {m}")
    for model_name in experiment.models:
        command[-1] += " \\"
        command.append(f"  --model {model_name}")
    return command


def build_task_section(
    experiment: ExperimentConfig,
    run_timestamp: str,
    output_root: Path,
    all_attempts: list[AttemptResult],
    metrics_by_run_dir: dict[str, dict] | None = None,
) -> str:
    metrics_by_run_dir = metrics_by_run_dir or {}

    grouped: dict[tuple[str, str, str, str], list[AttemptResult]] = {}
    for item in all_attempts:
        grouped.setdefault(
            (item.task_name, item.harness, item.model_name, item.reasoning_effort),
            [],
        ).append(item)

    grouped_stats: list[tuple[tuple[str, str, str, str], list[AttemptResult], float, float, int | None, float | None]] = []
    for key in sorted(grouped):
        attempts = sorted(grouped[key], key=lambda item: item.attempt)
        rewards = [item.reward for item in attempts]
        wall_times = [item.total_wall_time_sec for item in attempts if item.total_wall_time_sec is not None]
        mean_reward = statistics.mean(rewards)
        # Sample standard deviation across subtasks. `stdev` requires ≥2
        # samples; fall back to 0 for the 1-attempt case so we still emit a
        # finite cell instead of raising.
        reward_stdev = statistics.stdev(rewards) if len(rewards) >= 2 else 0.0
        # "Successes" only makes sense for binary-reward tasks (pass/fail).
        # For real-valued rewards (e.g. ROUGE-L, F1), rewards lie in (0, 1)
        # and no single attempt ever equals 1.0 exactly — counting them
        # would always give 0, which is misleading. Detect the real-valued
        # case by looking for any reward strictly between 0 and 1.
        has_fractional = any(0.0 < r < 1.0 for r in rewards)
        successes: int | None = None if has_fractional else sum(
            1 for item in attempts if item.passed
        )
        mean_wall_time = statistics.mean(wall_times) if wall_times else None
        grouped_stats.append(
            (key, attempts, mean_reward, reward_stdev, successes, mean_wall_time)
        )

    # Rank by mean reward desc, then successes desc (treating "n/a" as -1 so
    # it sorts below any real success count), then stdev asc (tighter
    # distributions preferred when other metrics tie).
    def _rank_successes(v: int | None) -> int:
        return -1 if v is None else v

    grouped_stats.sort(
        key=lambda item: (
            -item[2],
            -_rank_successes(item[4]),
            item[3],
            item[0][0],
            item[0][1],
            item[0][2],
            item[0][3],
        )
    )

    # User-requested metrics become columns. Two sources are tried per key:
    #   (a) per-trial scalar from each AttemptResult.rewards_raw (preferred
    #       — we can compute mean + sample stdev across subtasks)
    #   (b) aggregate-only value from the uv-script aggregator's metric.json
    #       (stored at result.json → stats.evals.<key>.metrics[0])
    metric_keys: tuple[str, ...] = experiment.metric_to_report
    # When the user provides --metric-to-report, they take responsibility for
    # what's reported; drop the default Mean reward / Reward stdev columns
    # so the table stays focused on their chosen metrics.
    emit_default_reward_cols = not metric_keys

    def _resolve_metric(
        m_key: str, attempts_list: list[AttemptResult], agg_metrics: dict
    ) -> tuple[str, str | None]:
        """Return (display_value, stdev_display) for one metric key.

        stdev_display is None when the metric is aggregate-only (no per-trial
        distribution to compute variance over).
        """
        per_trial_vals: list[float] = []
        for a in attempts_list:
            rd = dict(a.rewards_raw)
            v = rd.get(m_key)
            if isinstance(v, (int, float)):
                per_trial_vals.append(float(v))

        if per_trial_vals and len(per_trial_vals) == len(attempts_list):
            mean_v = statistics.mean(per_trial_vals)
            stdev_v = (
                statistics.stdev(per_trial_vals) if len(per_trial_vals) >= 2 else 0.0
            )
            return format_float(mean_v, 3), format_float(stdev_v, 3)

        agg_v = agg_metrics.get(m_key)
        if isinstance(agg_v, (int, float)):
            # Aggregate-only (e.g. pooled CheXbert F1) — no stdev available.
            return format_float(float(agg_v), 3), None
        return "", None

    aggregate_rows = []
    for key, attempts, mean_reward, reward_stdev, successes, mean_wall_time in grouped_stats:
        # All attempts in a group share the same run_dir (one Harbor job launch).
        run_dir_key = attempts[0].run_dir if attempts else ""
        agg_metrics = metrics_by_run_dir.get(run_dir_key, {}) or {}

        # Count unique subtasks the model was evaluated on, and the number
        # of attempts per subtask (typically == --attempts; variable only
        # when a subtask partially failed mid-sweep).
        distinct_subtasks = {a.subtask_name for a in attempts if a.subtask_name}
        sample_size = len(distinct_subtasks) or len(attempts)
        runs_total = len(attempts)
        # Integer division when attempts are uniform across subtasks. If
        # not uniform we fall back to mean (rounded) — rare but worth
        # surfacing correctly instead of a misleading integer.
        if sample_size and runs_total % sample_size == 0:
            n_runs = runs_total // sample_size
            n_runs_display = str(n_runs)
        else:
            n_runs_display = f"~{runs_total / max(sample_size, 1):.1f}"

        row = {
            "Task": key[0],
            "Harness": key[1],
            "Model": key[2],
            "Reasoning": key[3],
            "Runs": n_runs_display,
            "Sample size": str(sample_size),
        }
        if emit_default_reward_cols:
            row["Mean reward"] = format_float(mean_reward, 3)
            row["Reward stdev"] = format_float(reward_stdev, 3)
            row["Successes"] = "n/a" if successes is None else str(successes)
        row["Mean total wall time (s)"] = format_float(mean_wall_time, 2)

        for m_key in metric_keys:
            display, stdev_display = _resolve_metric(m_key, attempts, agg_metrics)
            row[m_key] = display
            if stdev_display is not None:
                row[f"{m_key}_stdev"] = stdev_display
        aggregate_rows.append(row)

    # Caption under the Aggregate Summary header so readers know exactly
    # where each column comes from.
    if metric_keys:
        # Classify each requested key by where its value came from, using the
        # first row as a representative sample.
        first_run_dir = grouped_stats[0][1][0].run_dir if grouped_stats else ""
        first_attempts = grouped_stats[0][1] if grouped_stats else []
        first_agg = metrics_by_run_dir.get(first_run_dir, {}) or {}
        per_trial_keys: list[str] = []
        aggregate_only_keys: list[str] = []
        for m_key in metric_keys:
            has_per_trial = any(
                isinstance(dict(a.rewards_raw).get(m_key), (int, float))
                for a in first_attempts
            )
            if has_per_trial:
                per_trial_keys.append(m_key)
            elif isinstance(first_agg.get(m_key), (int, float)):
                aggregate_only_keys.append(m_key)
        note_parts = []
        if per_trial_keys:
            note_parts.append(
                f"Per-trial metrics (mean ± sample stdev across subtasks): "
                f"{', '.join(f'`{k}`' for k in per_trial_keys)}."
            )
        if aggregate_only_keys:
            note_parts.append(
                f"Pooled aggregate metrics from the uv-script aggregator "
                f"(`<run_dir>/result.json → stats.evals.<key>.metrics[0]`; "
                f"no per-trial variance available): "
                f"{', '.join(f'`{k}`' for k in aggregate_only_keys)}."
            )
        reward_note = "\n\n".join(note_parts) if note_parts else ""
    else:
        reward_note = (
            "**Mean reward** = mean of the per-trial `reward` value "
            "emitted by each task's verifier."
        )

    detailed_rows = []
    for _, attempts, _, _, _, _ in grouped_stats:
        for item in attempts:
            row: dict[str, str] = {
                "Task": item.task_name,
                "Subtask": item.subtask_name,
                "Harness": item.harness,
                "Model": item.model_name,
                "Reasoning": item.reasoning_effort,
                "Attempt": str(item.attempt),
                "Reward": format_float(item.reward, 3),
                "Passed": "Yes" if item.passed else "No",
                "Exception type": item.exception_type,
            }
            # Surface per-trial scalars for any --metric-to-report key that
            # comes from the verifier's reward.json (e.g. f1, recall,
            # precision). Falls back to "" when the key isn't a per-trial
            # scalar (e.g. aggregator-only keys like `mean_f1`).
            rd = dict(item.rewards_raw)
            for m_key in metric_keys:
                v = rd.get(m_key)
                row[m_key] = format_float(v, 3) if isinstance(v, (int, float)) else ""
            row.update(
                {
                    "Total wall time (s)": format_float(item.total_wall_time_sec, 2),
                    "Input tokens": format_int(item.input_tokens),
                    "Cached tokens": format_int(item.cached_tokens),
                    "Output tokens": format_int(item.output_tokens),
                    "Run dir": f"`{item.run_dir}`" if item.run_dir else "",
                    "Trial dir": f"`{item.trial_dir}`" if item.trial_dir else "",
                }
            )
            detailed_rows.append(row)

    # Collect the actual run-dir basenames used for this render so readers
    # can trace any number back to raw Harbor output, even when --no-detailed
    # suppresses the per-attempt table.
    source_run_dirs = sorted(
        {
            Path(attempts[0].run_dir).name
            for _, attempts, *_ in grouped_stats
            if attempts and attempts[0].run_dir
        }
    )

    lines = [
        f"## {experiment.task_name}",
        "",
        f"- Task path: `{experiment.task_path}`",
        f"- Generated at: `{run_timestamp}`",
        f"- Raw results root: `{output_root}`",
    ]
    if source_run_dirs:
        lines.append("- Source run dirs:")
        for run_dir_name in source_run_dirs:
            lines.append(f"  - `{run_dir_name}`")
    for note in experiment.notes:
        lines.append(f"- Note: {note}")

    lines.extend(
        [
            "",
            "### Aggregate Summary",
            "",
            markdown_table(aggregate_rows),
            "",
        ]
        + ([reward_note, ""] if reward_note else [])
    )
    if experiment.include_detailed:
        lines.extend(
            [
                "### Detailed Attempts",
                "",
                markdown_table(detailed_rows),
                "",
            ]
        )
    lines.extend(
        [
            "### Reproducibility",
            "",
            "```bash",
            *build_repro_command(experiment, output_root),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def upsert_task_section(existing_text: str, task_name: str, task_section: str, title: str) -> str:
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


def build_experiment_config(args: argparse.Namespace, repo_root: Path) -> ExperimentConfig:
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
        include_detailed=args.include_detailed,
        metrics_script=args.metrics_script,
        concurrency=args.concurrency,
        subtasks=tuple(args.subtasks or ()),
        metric_to_report=tuple(args.metric_to_report or ()),
    )


def render_from_run_dirs(experiment: ExperimentConfig) -> None:
    all_attempts: list[AttemptResult] = []
    metrics_by_run_dir: dict[str, dict] = {}
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
        metrics_by_run_dir[str(run_dir)] = _load_run_dir_metric(run_dir)

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
            include_detailed=experiment.include_detailed,
            metrics_script=experiment.metrics_script,
            concurrency=experiment.concurrency,
            subtasks=experiment.subtasks,
            metric_to_report=experiment.metric_to_report,
        )

    write_baselines_markdown(
        experiment.baselines_md,
        task_name=report_experiment.task_name,
        task_section=build_task_section(
            report_experiment,
            make_timestamp(),
            experiment.output_root,
            all_attempts,
            metrics_by_run_dir=metrics_by_run_dir,
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
            run_dir=experiment.output_root / build_job_name(
                experiment.task_name, experiment.harness, model_name, timestamp
            ),
            launcher_log=experiment.output_root
            / (
                build_job_name(experiment.task_name, experiment.harness, model_name, timestamp)
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
    metrics_by_run_dir: dict[str, dict] = {}
    for spec, _, holder in processes:
        return_code = holder.get("returncode", 1)
        if return_code != 0:
            print(f"[{spec.harness}:{spec.model_name}] harbor exited with code {return_code}")
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
        metrics_by_run_dir[str(spec.run_dir)] = _load_run_dir_metric(spec.run_dir)

    write_baselines_markdown(
        experiment.baselines_md,
        task_name=experiment.task_name,
        task_section=build_task_section(
            experiment,
            timestamp,
            experiment.output_root,
            all_attempts,
            metrics_by_run_dir=metrics_by_run_dir,
        ),
        title=experiment.title,
    )

    print(f"Wrote baseline summary to {experiment.baselines_md}")
    for spec in specs:
        print(f"- {spec.harness}:{spec.model_name}: {spec.run_dir}")


if __name__ == "__main__":
    main()
