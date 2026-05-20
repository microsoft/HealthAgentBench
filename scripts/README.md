# Scripts

Operational scripts are grouped by integration or domain to keep this directory scalable.

Examples:
- top-level shared/bootstrap scripts (for example `setup_mimic.sh`)
- integration-specific scripts under `scripts/<integration>/` (for example `scripts/medagentbench/`)

## Baseline runners

Two top-level launchers run Harbor baselines across models/harnesses and append a generated section to [`paper/baselines.md`](../paper/baselines.md). Pick one based on the task's shape:

| Script | Use when |
| --- | --- |
| [`run_harbor_baselines.py`](run_harbor_baselines.py) | The benchmark is a single Harbor task directory (for example `tasks/mimic_iv_meds/`). |
| [`run_harbor_baselines_multitask.py`](run_harbor_baselines_multitask.py) | The benchmark is a parent directory whose immediate children are sibling subtasks that Harbor should enumerate (for example per-patient subdirs under `tasks/xray_report_gen/`). Supports `--subtask` to restrict to a subset and aggregates stats across subtasks. |

Both scripts share the same core flags: `--task-name`, `--task-path`, `--harness`, `--reasoning-effort`, `--attempts`, `--baselines-md`. Full flag list:

```bash
uv run python scripts/run_harbor_baselines.py --help
uv run python scripts/run_harbor_baselines_multitask.py --help
```

Minimal invocations:

```bash
# Single-task benchmark
uv run python scripts/run_harbor_baselines.py \
  --task-name mimic_iv_meds \
  --task-path tasks

# Multi-subtask benchmark (all subtasks)
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name xray_report_gen \
  --task-path tasks

# Multi-subtask benchmark, limited to two subtasks for debugging
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name xray_report_gen \
  --task-path tasks \
  --subtask p10046166_s50051329 \
  --subtask p10056223_s54015596
```

Notes:
- `paper/baselines.md` sections are auto-generated — do not hand-edit them. Re-run the launcher to refresh.
- Harbor Codex runs still expect a local Codex login on the host (`~/.codex/auth.json`); see [`CLAUDE.md`](../CLAUDE.md) for details.
