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

## tumor_area_selection_pathology

- Task path: `tasks`
- Generated at: `20260503T000750Z`
- Raw results root: `/mnt/hanoverdev/data/jose/medcli_outputs/tumor_area_selection_pathology/runs`
- Source run dirs:
  - `tumor_area_selection_pathology__codex__gpt-5.3-codex__20260501T223500Z`
  - `tumor_area_selection_pathology__claude-code__claude-sonnet-4-6__20260505T232005Z`

### Aggregate Summary

| Task | Harness | Model | Reasoning | Runs | Sample size | Mean total wall time (s) | tcga_slide_precision | tcga_slide_recall | tcga_slide_f1 | camelyon_tile_precision | camelyon_tile_recall | camelyon_tile_f1 | camelyon_tumor_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tumor_area_selection_pathology | codex | gpt-5.3-codex | medium | 1 | 35 | 197.19 | 0.727 | 0.615 | 0.667 | 0.488 | 0.740 | 0.588 | 0.565 |
| tumor_area_selection_pathology | claude-code | claude-sonnet-4-6 | medium | 1 | 35 | 276.15 | 0.565 | 1.000 | 0.722 | 0.693 | 0.492 | 0.576 | 0.338 |

Pooled aggregate metrics from the uv-script aggregator (`<run_dir>/result.json → stats.evals.<key>.metrics[0]`; no per-trial variance available): `tcga_slide_precision`, `tcga_slide_recall`, `tcga_slide_f1`, `camelyon_tile_precision`, `camelyon_tile_recall`, `camelyon_tile_f1`, `camelyon_tumor_coverage`.

### Reproducibility

```bash
uv run python scripts/run_harbor_baselines_multitask.py \
  --mode render \
  --task-name tumor_area_selection_pathology \
  --task-path tasks \
  --harness codex \
  --output-root /mnt/hanoverdev/data/jose/medcli_outputs/tumor_area_selection_pathology/runs \
  --attempts 1 \
  --reasoning-effort medium \
  --baselines-md paper/baselines.md \
  --metrics-script scripts/tumor_area_selection_pathology/aggregate_metric.py \
  --no-detailed \
  --run-dir /mnt/hanoverdev/data/jose/medcli_outputs/tumor_area_selection_pathology/runs/tumor_area_selection_pathology__codex__gpt-5.3-codex__20260501T223500Z \
  --run-dir /mnt/hanoverdev/data/jose/medcli_outputs/tumor_area_selection_pathology/runs/tumor_area_selection_pathology__claude-code__claude-sonnet-4-6__20260505T232005Z \
  --metric-to-report tcga_slide_precision \
  --metric-to-report tcga_slide_recall \
  --metric-to-report tcga_slide_f1 \
  --metric-to-report camelyon_tile_precision \
  --metric-to-report camelyon_tile_recall \
  --metric-to-report camelyon_tile_f1 \
  --metric-to-report camelyon_tumor_coverage
```

## mimic_iv_dq

- Task path: `tasks`
- Generated at: `20260501T195026Z`
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
  --no-detailed \
  --metric-to-report f1 \
  --metric-to-report recall \
  --metric-to-report precision \
  --model gpt-5.4 \
  --model gpt-5.4-mini
```
