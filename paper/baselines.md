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

## mimic_report_gen

- Task path: `tasks`
- Generated at: `20260417T175549Z`
- Raw results root: `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_report_gen`
- Source run dirs:
  - `mimic_report_gen__codex__gpt-5.3-codex__20260416T231648Z`
  - `mimic_report_gen__codex__gpt-5.4__20260416T231648Z`

### Aggregate Summary

| Task | Harness | Model | Reasoning | Runs | Sample size | Mean total wall time (s) | avg_rouge_l | avg_rouge_l_stdev | chexbert_f1_5_micro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mimic_report_gen | codex | gpt-5.4 | medium | 1 | 141 | 489.72 | 0.246 | 0.071 | 51.220 |
| mimic_report_gen | codex | gpt-5.3-codex | medium | 1 | 141 | 431.13 | 0.222 | 0.059 | 55.000 |

Per-trial metrics (mean ± sample stdev across subtasks): `avg_rouge_l`.

Pooled aggregate metrics from the uv-script aggregator (`<run_dir>/result.json → stats.evals.<key>.metrics[0]`; no per-trial variance available): `chexbert_f1_5_micro_f1`.

### Reproducibility

```bash
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_report_gen \
  --task-path tasks \
  --harness codex \
  --output-root /mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_report_gen \
  --attempts 1 \
  --reasoning-effort medium \
  --no-detailed \
  --metric-to-report avg_rouge_l \
  --metric-to-report chexbert_f1_5_micro_f1 \
  --model gpt-5.3-codex \
  --model gpt-5.4
```

## mimic_iv_dq

- Task path: `tasks`
- Generated at: `20260501T171926Z`
- Raw results root: `/home/qianchuliu/projects/MedCLI/results/baselines/mimic_iv_dq`
- Source run dirs:
  - `mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z`
  - `mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z`
  - `mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z`
  - `mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z`
  - `mimic_iv_dq__codex__gpt-5.4__20260430T223339Z`
  - `mimic_iv_dq__codex__gpt-5.5__20260430T223339Z`

### Aggregate Summary

| Task | Harness | Model | Reasoning | Runs | Sample size | Mean total wall time (s) | f1 | f1_stdev | recall | recall_stdev | precision | precision_stdev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mimic_iv_dq | codex | gpt-5.5 | medium | 3 | 4 | 484.83 | 0.443 | 0.213 | 0.355 | 0.201 | 0.711 | 0.305 |
| mimic_iv_dq | claude-code | claude-sonnet-4-6 | medium | 3 | 4 | 616.24 | 0.382 | 0.227 | 0.339 | 0.186 | 0.602 | 0.383 |
| mimic_iv_dq | claude-code | claude-opus-4-7 | medium | 3 | 4 | 282.09 | 0.282 | 0.210 | 0.218 | 0.164 | 0.592 | 0.378 |
| mimic_iv_dq | claude-code | claude-opus-4-6 | medium | 3 | 4 | 690.25 | 0.280 | 0.255 | 0.376 | 0.254 | 0.372 | 0.414 |
| mimic_iv_dq | codex | gpt-5.4 | medium | 3 | 4 | 572.47 | 0.196 | 0.040 | 0.128 | 0.040 | 0.632 | 0.345 |
| mimic_iv_dq | codex | gpt-5.3-codex | medium | 3 | 4 | 316.03 | 0.164 | 0.064 | 0.102 | 0.049 | 0.737 | 0.319 |

Per-trial metrics (mean ± sample stdev across subtasks): `f1`, `recall`, `precision`.

### Detailed Attempts

| Task | Subtask | Harness | Model | Reasoning | Attempt | Reward | Passed | Exception type | f1 | recall | precision | Total wall time (s) | Input tokens | Cached tokens | Output tokens | Run dir | Trial dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.5 | medium | 1 | 0.500 | No |  | 0.500 | 0.333 | 1.000 | 423.79 | 581087 | 469248 | 8163 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_demographic_conflict__Gip7ZTm` |
| mimic_iv_dq | task_combined | codex | gpt-5.5 | medium | 2 | 0.268 | No |  | 0.268 | 0.191 | 0.448 | 664.74 | 2534644 | 2286208 | 11684 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_combined__FkjdVEG` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.5 | medium | 3 | 0.836 | No |  | 0.836 | 0.719 | 1.000 | 561.52 | 2633895 | 2481408 | 10933 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_inconsistency__zuH4g7b` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.5 | medium | 4 | 0.406 | No |  | 0.406 | 0.382 | 0.433 | 504.36 | 903869 | 821504 | 9356 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_impossible_value__pKqiRLs` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.5 | medium | 5 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 402.23 | 1971889 | 1817216 | 9660 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_demographic_conflict__GiD8W3V` |
| mimic_iv_dq | task_combined | codex | gpt-5.5 | medium | 6 | 0.224 | No |  | 0.224 | 0.162 | 0.367 | 462.03 | 2495091 | 2308992 | 12656 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_combined__pdPGJ9x` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.5 | medium | 7 | 0.836 | No |  | 0.836 | 0.719 | 1.000 | 467.61 | 1159258 | 1031296 | 11540 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_inconsistency__Kmke32y` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.5 | medium | 8 | 0.515 | No |  | 0.515 | 0.500 | 0.531 | 463.20 | 2458860 | 2342144 | 12671 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_impossible_value__56ZDS3f` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.5 | medium | 9 | 0.500 | No |  | 0.500 | 0.333 | 1.000 | 322.86 | 820576 | 699136 | 8281 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_demographic_conflict__rS3otHV` |
| mimic_iv_dq | task_combined | codex | gpt-5.5 | medium | 10 | 0.267 | No |  | 0.267 | 0.206 | 0.378 | 585.69 | 4193199 | 3990528 | 12502 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_combined__kPTzSmc` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.5 | medium | 11 | 0.400 | No |  | 0.400 | 0.250 | 1.000 | 530.40 | 1295973 | 1208448 | 9980 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_inconsistency__wY5yFjz` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.5 | medium | 12 | 0.364 | No |  | 0.364 | 0.353 | 0.375 | 429.53 | 1941772 | 1838976 | 10663 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.5__20260430T223339Z/task_impossible_value__KzidkBs` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-sonnet-4-6 | medium | 1 | 0.560 | No |  | 0.560 | 0.389 | 1.000 | 216.90 | 52028 | 49835 | 1644 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_demographic_conflict__shjYypa` |
| mimic_iv_dq | task_combined | claude-code | claude-sonnet-4-6 | medium | 2 | 0.264 | No |  | 0.264 | 0.176 | 0.522 | 946.08 | 353065 | 309223 | 18381 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_combined__AE3QZmF` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-sonnet-4-6 | medium | 3 | 0.286 | No |  | 0.286 | 0.594 | 0.188 | 654.74 | 198223 | 177918 | 7820 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_inconsistency__XK3cjmi` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-sonnet-4-6 | medium | 4 | 0.225 | No |  | 0.225 | 0.235 | 0.216 | 632.32 | 138356 | 108919 | 4124 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_impossible_value__LkYGHdm` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-sonnet-4-6 | medium | 5 | 0.615 | No |  | 0.615 | 0.444 | 1.000 | 236.13 | 75695 | 70254 | 3377 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_demographic_conflict__aqT8jMQ` |
| mimic_iv_dq | task_combined | claude-code | claude-sonnet-4-6 | medium | 6 | 0.161 | No |  | 0.161 | 0.162 | 0.159 | 1041.04 | 537065 | 478769 | 22888 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_combined__uXTSLRR` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-sonnet-4-6 | medium | 7 | 0.730 | No |  | 0.730 | 0.594 | 0.947 | 241.62 | 113964 | 106266 | 3473 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_inconsistency__6r5StP6` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-sonnet-4-6 | medium | 8 | 0.254 | No |  | 0.254 | 0.235 | 0.276 | 621.35 | 95689 | 87564 | 5215 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_impossible_value__AkvAG9W` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-sonnet-4-6 | medium | 9 | 0.105 | No |  | 0.105 | 0.056 | 1.000 | 414.45 | 119500 | 109472 | 4832 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_demographic_conflict__EGB7HMi` |
| mimic_iv_dq | task_combined | claude-code | claude-sonnet-4-6 | medium | 10 | 0.505 | No |  | 0.505 | 0.353 | 0.889 | 703.06 | 1409032 | 1317484 | 40795 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_combined__c376XkN` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-sonnet-4-6 | medium | 11 | 0.715 | No |  | 0.715 | 0.594 | 0.900 | 873.05 | 170089 | 151511 | 7027 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_inconsistency__CHuFxu6` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-sonnet-4-6 | medium | 12 | 0.168 | No |  | 0.168 | 0.235 | 0.131 | 814.09 | 2452186 | 2352842 | 36470 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-sonnet-4-6__20260501T014356Z/task_impossible_value__tT9zKRE` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-opus-4-7 | medium | 1 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 220.65 | 444504 | 431478 | 7457 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_demographic_conflict__ERtfSXH` |
| mimic_iv_dq | task_combined | claude-code | claude-opus-4-7 | medium | 2 | 0.220 | No |  | 0.220 | 0.147 | 0.435 | 443.84 | 1271951 | 1239682 | 17812 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_combined__DY4GPPZ` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-opus-4-7 | medium | 3 | 0.730 | No |  | 0.730 | 0.594 | 0.947 | 197.11 | 523587 | 507627 | 8097 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_inconsistency__5whMTAS` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-opus-4-7 | medium | 4 | 0.364 | No |  | 0.364 | 0.294 | 0.476 | 279.84 | 800315 | 760657 | 14044 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_impossible_value__BVsPuDn` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-opus-4-7 | medium | 5 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 142.71 | 339032 | 332262 | 4883 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_demographic_conflict__sUShsfW` |
| mimic_iv_dq | task_combined | claude-code | claude-opus-4-7 | medium | 6 | 0.184 | No |  | 0.184 | 0.132 | 0.300 | 397.26 | 1478648 | 1442206 | 20858 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_combined__Y3736ir` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-opus-4-7 | medium | 7 | 0.667 | No |  | 0.667 | 0.500 | 1.000 | 305.16 | 889321 | 866875 | 14568 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_inconsistency__e3FikFY` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-opus-4-7 | medium | 8 | 0.140 | No |  | 0.140 | 0.118 | 0.174 | 255.52 | 642193 | 623625 | 10523 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_impossible_value__pXnRim4` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-opus-4-7 | medium | 9 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 204.27 | 592477 | 577932 | 9150 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_demographic_conflict__QpxhHFs` |
| mimic_iv_dq | task_combined | claude-code | claude-opus-4-7 | medium | 10 | 0.250 | No |  | 0.250 | 0.162 | 0.550 | 428.08 | 1905105 | 1855485 | 23057 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_combined__GEHLdYc` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-opus-4-7 | medium | 11 | 0.016 | No |  | 0.016 | 0.125 | 0.009 | 212.92 | 515523 | 498500 | 9181 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_inconsistency__rsNEf4d` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-opus-4-7 | medium | 12 | 0.212 | No |  | 0.212 | 0.206 | 0.219 | 297.68 | 553784 | 529043 | 15173 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-7__20260501T014356Z/task_impossible_value__qQwmH8B` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-opus-4-6 | medium | 1 | 0.560 | No |  | 0.560 | 0.389 | 1.000 | 373.09 | 537660 | 511374 | 12701 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_demographic_conflict__kKuF5T5` |
| mimic_iv_dq | task_combined | claude-code | claude-opus-4-6 | medium | 2 | 0.059 | No |  | 0.059 | 0.118 | 0.039 | 676.53 | 829021 | 760193 | 27725 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_combined__DTqSYy2` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-opus-4-6 | medium | 3 | 0.116 | No |  | 0.116 | 0.625 | 0.064 | 314.06 | 367626 | 339843 | 10815 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_inconsistency__pxjpMc4` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-opus-4-6 | medium | 4 | 0.267 | No |  | 0.267 | 0.235 | 0.308 | 622.90 | 730555 | 677551 | 26589 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_impossible_value__j4PkarF` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-opus-4-6 | medium | 5 | 0.364 | No |  | 0.364 | 0.222 | 1.000 | 526.69 | 1174581 | 1140109 | 20781 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_demographic_conflict__u9CRpza` |
| mimic_iv_dq | task_combined | claude-code | claude-opus-4-6 | medium | 6 | 0.046 | No |  | 0.046 | 0.176 | 0.026 | 906.92 | 1766925 | 1691312 | 36293 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_combined__4tHHmtg` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-opus-4-6 | medium | 7 | 0.753 | No |  | 0.753 | 1.000 | 0.604 | 1109.62 | 2037453 | 1950484 | 43504 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_inconsistency__TLMPbgE` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-opus-4-6 | medium | 8 | 0.158 | No |  | 0.158 | 0.235 | 0.119 | 856.78 | 2099502 | 2023635 | 35950 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_impossible_value__5cpxYbo` |
| mimic_iv_dq | task_demographic_conflict | claude-code | claude-opus-4-6 | medium | 9 | 0.667 | No |  | 0.667 | 0.500 | 1.000 | 415.00 | 694098 | 666516 | 15645 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_demographic_conflict__VVLUHdP` |
| mimic_iv_dq | task_combined | claude-code | claude-opus-4-6 | medium | 10 | 0.052 | No |  | 0.052 | 0.162 | 0.031 | 949.64 | 2335106 | 2247612 | 39908 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_combined__rnvBi33` |
| mimic_iv_dq | task_inconsistency | claude-code | claude-opus-4-6 | medium | 11 | 0.033 | No |  | 0.033 | 0.531 | 0.017 | 1057.30 | 2315848 | 2253074 | 35599 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_inconsistency__fuZnqzA` |
| mimic_iv_dq | task_impossible_value | claude-code | claude-opus-4-6 | medium | 12 | 0.282 | No |  | 0.282 | 0.324 | 0.250 | 474.44 | 645701 | 566729 | 20262 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__claude-code__claude-opus-4-6__20260501T014356Z/task_impossible_value__LKAubGx` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.4 | medium | 1 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 605.63 | 819865 | 770688 | 12209 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_demographic_conflict__2MbGb92` |
| mimic_iv_dq | task_combined | codex | gpt-5.4 | medium | 2 | 0.253 | No |  | 0.253 | 0.162 | 0.579 | 789.72 | 1663042 | 1593600 | 15687 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_combined__pEfAGxg` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.4 | medium | 3 | 0.091 | No |  | 0.091 | 0.062 | 0.167 | 783.77 | 2292630 | 2147072 | 20472 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_inconsistency__XFj4XZq` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.4 | medium | 4 | 0.214 | No |  | 0.214 | 0.176 | 0.273 | 619.25 | 1385659 | 1315328 | 13785 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_impossible_value__U5HodU3` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.4 | medium | 5 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 476.94 | 1213985 | 1153792 | 12448 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_demographic_conflict__XG8T6qU` |
| mimic_iv_dq | task_combined | codex | gpt-5.4 | medium | 6 | 0.212 | No |  | 0.212 | 0.132 | 0.529 | 638.75 | 1835054 | 1757312 | 17197 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_combined__M8SaoRB` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.4 | medium | 7 | 0.171 | No |  | 0.171 | 0.094 | 1.000 | 603.83 | 2004850 | 1892736 | 16084 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_inconsistency__X7RKuGa` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.4 | medium | 8 | 0.233 | No |  | 0.233 | 0.206 | 0.269 | 502.48 | 1445746 | 1363584 | 12197 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_impossible_value__tD8iUEG` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.4 | medium | 9 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 484.23 | 1026638 | 976128 | 12533 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_demographic_conflict__v8Eennp` |
| mimic_iv_dq | task_combined | codex | gpt-5.4 | medium | 10 | 0.207 | No |  | 0.207 | 0.132 | 0.474 | 646.12 | 2072918 | 1995776 | 18073 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_combined__AExc69K` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.4 | medium | 11 | 0.171 | No |  | 0.171 | 0.094 | 1.000 | 378.43 | 453595 | 413696 | 8686 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_inconsistency__7DUwNjT` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.4 | medium | 12 | 0.196 | No |  | 0.196 | 0.147 | 0.294 | 340.45 | 395584 | 362112 | 8358 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.4__20260430T223339Z/task_impossible_value__HuXqP2Q` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.3-codex | medium | 1 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 329.16 | 185494 | 171136 | 4776 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_demographic_conflict__Nox4g7y` |
| mimic_iv_dq | task_combined | codex | gpt-5.3-codex | medium | 2 | 0.152 | No |  | 0.152 | 0.088 | 0.545 | 459.41 | 397215 | 360448 | 7662 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_combined__An47c9P` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.3-codex | medium | 3 | 0.061 | No |  | 0.061 | 0.031 | 1.000 | 356.10 | 181251 | 169088 | 6114 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_inconsistency__tffzwRq` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.3-codex | medium | 4 | 0.125 | No |  | 0.125 | 0.088 | 0.214 | 318.74 | 336948 | 303744 | 4693 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_impossible_value__U3RHLqT` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.3-codex | medium | 5 | 0.200 | No |  | 0.200 | 0.111 | 1.000 | 343.07 | 160600 | 141696 | 5111 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_demographic_conflict__2Mj4NJC` |
| mimic_iv_dq | task_combined | codex | gpt-5.3-codex | medium | 6 | 0.208 | No |  | 0.208 | 0.118 | 0.889 | 337.57 | 323810 | 288384 | 7331 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_combined__Kd5Sa55` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.3-codex | medium | 7 | 0.061 | No |  | 0.061 | 0.031 | 1.000 | 279.95 | 237503 | 219008 | 7107 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_inconsistency__xLFgZBS` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.3-codex | medium | 8 | 0.245 | No |  | 0.245 | 0.176 | 0.400 | 268.00 | 546453 | 490240 | 6086 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_impossible_value__JjreW6k` |
| mimic_iv_dq | task_demographic_conflict | codex | gpt-5.3-codex | medium | 9 | 0.105 | No |  | 0.105 | 0.056 | 1.000 | 253.64 | 235214 | 220416 | 5008 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_demographic_conflict__z6QLJiw` |
| mimic_iv_dq | task_combined | codex | gpt-5.3-codex | medium | 10 | 0.230 | No |  | 0.230 | 0.147 | 0.526 | 336.53 | 718104 | 666880 | 8042 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_combined__EFkh5J6` |
| mimic_iv_dq | task_inconsistency | codex | gpt-5.3-codex | medium | 11 | 0.171 | No |  | 0.171 | 0.094 | 1.000 | 313.18 | 338840 | 313472 | 8274 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_inconsistency__LRh2Wep` |
| mimic_iv_dq | task_impossible_value | codex | gpt-5.3-codex | medium | 12 | 0.214 | No |  | 0.214 | 0.176 | 0.273 | 196.98 | 164481 | 140416 | 3974 | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z` | `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/mimic_iv_dq/mimic_iv_dq__codex__gpt-5.3-codex__20260430T223339Z/task_impossible_value__GYNZ2Xt` |

### Reproducibility

```bash
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_iv_dq \
  --task-path tasks \
  --harness codex \
  --output-root /home/qianchuliu/projects/MedCLI/results/baselines/mimic_iv_dq \
  --attempts 3 \
  --reasoning-effort medium \
  --metrics-script scripts/mimic_iv_dq/aggregate_metric.py \
  --metric-to-report f1 \
  --metric-to-report recall \
  --metric-to-report precision \
  --model gpt-5.4 \
  --model gpt-5.4-mini
```
