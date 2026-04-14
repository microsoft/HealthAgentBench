# Baselines

Harbor baseline runs across tasks and installed-agent harnesses, generated with [`scripts/run_harbor_baselines.py`](../scripts/run_harbor_baselines.py).

## mimic_iv_meds

- Task path: `tasks`
- Generated at: `20260409T205239Z`
- Raw results root: `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds`

### Aggregate Summary

| Task | Harness | Model | Reasoning | Runs | Mean reward | Reward variance | Successes | Mean total wall time (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mimic_iv_meds | copilot-cli | gpt-5.4 | medium | 3 | 1.000 | 0.000 | 3 | 415.02 |
| mimic_iv_meds | copilot-cli | gpt-5.4-mini | medium | 3 | 0.667 | 0.222 | 2 | 347.91 |
| mimic_iv_meds | copilot-cli | claude-haiku-4.5 | medium | 3 | 0.000 | 0.000 | 0 | 45.24 |
| mimic_iv_meds | copilot-cli | claude-opus-4.6 | medium | 3 | 0.000 | 0.000 | 0 | 185.14 |
| mimic_iv_meds | copilot-cli | claude-sonnet-4.6 | medium | 3 | 0.000 | 0.000 | 0 | 253.04 |

### Detailed Attempts

| Task | Harness | Model | Reasoning | Attempt | Reward | Passed | Exception type | Total wall time (s) | Input tokens | Cached tokens | Output tokens | Run dir | Trial dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mimic_iv_meds | copilot-cli | gpt-5.4 | medium | 1 | 1.000 | Yes |  | 457.03 | 1255804 | 1190528 | 11330 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4__20260409T201716Z/mimic_iv_meds__4tnyNfq` |
| mimic_iv_meds | copilot-cli | gpt-5.4 | medium | 2 | 1.000 | Yes |  | 382.16 | 918527 | 886656 | 10889 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4__20260409T201716Z/mimic_iv_meds__TbPex6f` |
| mimic_iv_meds | copilot-cli | gpt-5.4 | medium | 3 | 1.000 | Yes |  | 405.85 | 821145 | 790784 | 9314 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4__20260409T201716Z/mimic_iv_meds__akrceoD` |
| mimic_iv_meds | copilot-cli | gpt-5.4-mini | medium | 1 | 1.000 | Yes |  | 280.96 | 1457950 | 1391616 | 13538 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4-mini__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4-mini__20260409T201716Z/mimic_iv_meds__4qv35Bm` |
| mimic_iv_meds | copilot-cli | gpt-5.4-mini | medium | 2 | 0.000 | No |  | 203.14 | 704299 | 676352 | 12580 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4-mini__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4-mini__20260409T201716Z/mimic_iv_meds__SnvgPYu` |
| mimic_iv_meds | copilot-cli | gpt-5.4-mini | medium | 3 | 1.000 | Yes |  | 559.61 | 1333144 | 1241088 | 12173 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4-mini__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__gpt-5.4-mini__20260409T201716Z/mimic_iv_meds__DG7hK4T` |
| mimic_iv_meds | copilot-cli | claude-haiku-4.5 | medium | 1 | 0.000 | No | NonZeroAgentExitCodeError | 53.11 |  |  |  | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-haiku-4.5__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-haiku-4.5__20260409T201716Z/mimic_iv_meds__4gEzFuk` |
| mimic_iv_meds | copilot-cli | claude-haiku-4.5 | medium | 2 | 0.000 | No | NonZeroAgentExitCodeError | 39.50 |  |  |  | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-haiku-4.5__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-haiku-4.5__20260409T201716Z/mimic_iv_meds__9ZkKsMj` |
| mimic_iv_meds | copilot-cli | claude-haiku-4.5 | medium | 3 | 0.000 | No | NonZeroAgentExitCodeError | 43.10 |  |  |  | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-haiku-4.5__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-haiku-4.5__20260409T201716Z/mimic_iv_meds__oQc6Vcr` |
| mimic_iv_meds | copilot-cli | claude-opus-4.6 | medium | 1 | 0.000 | No |  | 203.82 | 801435 | 685972 | 5378 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-opus-4.6__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-opus-4.6__20260409T201716Z/mimic_iv_meds__wRoU9wK` |
| mimic_iv_meds | copilot-cli | claude-opus-4.6 | medium | 2 | 0.000 | No |  | 172.47 | 688939 | 627417 | 4899 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-opus-4.6__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-opus-4.6__20260409T201716Z/mimic_iv_meds__pepmm8i` |
| mimic_iv_meds | copilot-cli | claude-opus-4.6 | medium | 3 | 0.000 | No |  | 179.13 | 610461 | 531975 | 5712 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-opus-4.6__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-opus-4.6__20260409T201716Z/mimic_iv_meds__cTUQ2H2` |
| mimic_iv_meds | copilot-cli | claude-sonnet-4.6 | medium | 1 | 0.000 | No |  | 277.29 | 783678 | 686140 | 6855 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-sonnet-4.6__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-sonnet-4.6__20260409T201716Z/mimic_iv_meds__adqRBB2` |
| mimic_iv_meds | copilot-cli | claude-sonnet-4.6 | medium | 2 | 0.000 | No |  | 239.32 | 666214 | 601647 | 9064 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-sonnet-4.6__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-sonnet-4.6__20260409T201716Z/mimic_iv_meds__hDh8zCL` |
| mimic_iv_meds | copilot-cli | claude-sonnet-4.6 | medium | 3 | 0.000 | No |  | 242.52 | 640811 | 586205 | 9325 | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-sonnet-4.6__20260409T201716Z` | `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds/mimic_iv_meds__copilot-cli__claude-sonnet-4.6__20260409T201716Z/mimic_iv_meds__ibh7X2E` |

### Reproducibility

```bash
uv run python scripts/run_harbor_baselines.py \
  --task-name mimic_iv_meds \
  --task-path tasks \
  --harness copilot-cli \
  --output-root /mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds \
  --attempts 3 \
  --reasoning-effort medium \
  --model claude-haiku-4.5 \
  --model claude-opus-4.6 \
  --model claude-sonnet-4.6 \
  --model gpt-5.4 \
  --model gpt-5.4-mini
```
