# Baselines

Harbor baseline runs across tasks and installed-agent harnesses, generated with [`scripts/run_harbor_baselines.py`](../scripts/run_harbor_baselines.py).

## mimic_iv_meds

- Task path: `tasks`
- Generated at: `20260527T183216Z`
- Raw results root: `/mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds`
- Source run dirs:
  - `mimic_iv_meds__claude-code__claude-opus-4-6__20260527T172546Z`
  - `mimic_iv_meds__claude-code__claude-opus-4-6__20260527T181803Z`
  - `mimic_iv_meds__claude-code__claude-opus-4-7__20260527T172546Z`
  - `mimic_iv_meds__claude-code__claude-opus-4-7__20260527T181803Z`
  - `mimic_iv_meds__claude-code__claude-sonnet-4-6__20260527T172546Z`
  - `mimic_iv_meds__claude-code__claude-sonnet-4-6__20260527T181803Z`
  - `mimic_iv_meds__codex__gpt-5.3-codex__20260527T173252Z`
  - `mimic_iv_meds__codex__gpt-5.3-codex__20260527T182452Z`
  - `mimic_iv_meds__codex__gpt-5.4-mini__20260527T173252Z`
  - `mimic_iv_meds__codex__gpt-5.4-mini__20260527T182452Z`
  - `mimic_iv_meds__codex__gpt-5.4__20260527T173252Z`
  - `mimic_iv_meds__codex__gpt-5.4__20260527T182452Z`

### Aggregate Summary

| Task | Harness | Model | Reasoning | Runs | Sample size | Mean reward | Reward stdev | Successes | Mean total wall time (s) | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mimic_iv_meds | claude-code | claude-opus-4-7 | medium | 3 | 1 | 1.000 | 0.000 | 3 | 257.29 | 0.9682 |
| mimic_iv_meds | claude-code | claude-opus-4-7 | xhigh | 3 | 1 | 1.000 | 0.000 | 3 | 342.70 | 2.0179 |
| mimic_iv_meds | claude-code | claude-sonnet-4-6 | xhigh | 3 | 1 | 1.000 | 0.000 | 3 | 380.29 | 0.6488 |
| mimic_iv_meds | codex | gpt-5.3-codex | medium | 3 | 1 | 1.000 | 0.000 | 3 | 355.22 | 0.3487 |
| mimic_iv_meds | codex | gpt-5.3-codex | xhigh | 3 | 1 | 1.000 | 0.000 | 3 | 443.98 | 0.3871 |
| mimic_iv_meds | claude-code | claude-sonnet-4-6 | medium | 3 | 1 | 0.667 | 0.577 | 2 | 358.78 | 0.5696 |
| mimic_iv_meds | codex | gpt-5.4 | medium | 3 | 1 | 0.667 | 0.577 | 2 | 353.68 | 0.4266 |
| mimic_iv_meds | codex | gpt-5.4 | xhigh | 3 | 1 | 0.667 | 0.577 | 2 | 466.88 | 0.6579 |
| mimic_iv_meds | codex | gpt-5.4-mini | xhigh | 3 | 1 | 0.667 | 0.577 | 2 | 760.81 | 0.4666 |
| mimic_iv_meds | codex | gpt-5.4-mini | medium | 3 | 1 | 0.333 | 0.577 | 1 | 366.78 | 0.1654 |
| mimic_iv_meds | claude-code | claude-opus-4-6 | medium | 3 | 1 | 0.000 | 0.000 | 0 | 328.45 | 0.8552 |
| mimic_iv_meds | claude-code | claude-opus-4-6 | xhigh | 3 | 1 | 0.000 | 0.000 | 0 | 334.17 | 0.8219 |

**Mean reward** = mean of the per-trial `reward` value emitted by each task's verifier.

### Reproducibility

Four phases: claude-code and codex sweeps at each of two effort levels (medium, xhigh), then a single render-mode merge.

```bash
# Phase A — claude-code @ xhigh
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_iv_meds --task-path tasks --harness claude-code \
  --output-root /mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds \
  --attempts 3 --concurrency 3 --reasoning-effort xhigh --no-detailed \
  --model claude-opus-4-7 --model claude-opus-4-6 --model claude-sonnet-4-6

# Phase B — codex @ xhigh
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_iv_meds --task-path tasks --harness codex \
  --output-root /mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds \
  --attempts 3 --concurrency 3 --reasoning-effort xhigh --no-detailed \
  --model gpt-5.4 --model gpt-5.3-codex --model gpt-5.4-mini

# Phase A' — claude-code @ medium
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_iv_meds --task-path tasks --harness claude-code \
  --output-root /mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds \
  --attempts 3 --concurrency 3 --reasoning-effort medium --no-detailed \
  --model claude-opus-4-7 --model claude-opus-4-6 --model claude-sonnet-4-6

# Phase B' — codex @ medium
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_iv_meds --task-path tasks --harness codex \
  --output-root /mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds \
  --attempts 3 --concurrency 3 --reasoning-effort medium --no-detailed \
  --model gpt-5.4 --model gpt-5.3-codex --model gpt-5.4-mini

# Phase C — merge all 12 run dirs into the final 12-row table
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name mimic_iv_meds --task-path tasks --harness codex --mode render \
  --output-root /mnt/hanoverdev/scratch/shengz/medcli/results/mimic_iv_meds \
  --attempts 3 --reasoning-effort xhigh --no-detailed \
  --baselines-md paper/baselines.md \
  --run-dir <Phase A:  claude-code  claude-opus-4-7   xhigh  run dir> \
  --run-dir <Phase A:  claude-code  claude-opus-4-6   xhigh  run dir> \
  --run-dir <Phase A:  claude-code  claude-sonnet-4-6 xhigh  run dir> \
  --run-dir <Phase B:  codex        gpt-5.4           xhigh  run dir> \
  --run-dir <Phase B:  codex        gpt-5.3-codex     xhigh  run dir> \
  --run-dir <Phase B:  codex        gpt-5.4-mini      xhigh  run dir> \
  --run-dir <Phase A': claude-code  claude-opus-4-7   medium run dir> \
  --run-dir <Phase A': claude-code  claude-opus-4-6   medium run dir> \
  --run-dir <Phase A': claude-code  claude-sonnet-4-6 medium run dir> \
  --run-dir <Phase B': codex        gpt-5.4           medium run dir> \
  --run-dir <Phase B': codex        gpt-5.3-codex     medium run dir> \
  --run-dir <Phase B': codex        gpt-5.4-mini      medium run dir>
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

## clinical_trial_matching

- Task path: `tasks`
- Generated at: `20260505T215435Z`
- Raw results root: `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/clinical_trial_matching`
- Source run dirs:
  - `clinical_trial_matching__claude-code__claude-opus-4-7__20260505T014830Z`
  - `clinical_trial_matching__claude-code__claude-sonnet-4-6__20260505T014830Z`
  - `clinical_trial_matching__codex__gpt-5.3-codex__20260505T203426Z`
  - `clinical_trial_matching__codex__gpt-5.4__20260505T203426Z`
  - `clinical_trial_matching__codex__gpt-5.5__20260505T203426Z`

### Aggregate Summary

| Task | Harness | Model | Reasoning | Runs | Sample size | Mean total wall time (s) | ndcg_at_10 | ndcg_at_10_stdev | success | reward | reward_stdev | f1 | f1_stdev | precision | precision_stdev | recall | recall_stdev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_trial_matching | codex | gpt-5.5 | medium | 1 | 10 | 385.26 | 0.928 | 0.082 | 4.000 | 0.400 | 0.516 | 0.402 | 0.146 | 0.776 | 0.151 | 0.290 | 0.137 |
| clinical_trial_matching | codex | gpt-5.4 | medium | 1 | 10 | 346.35 | 0.849 | 0.173 | 3.000 | 0.300 | 0.483 | 0.197 | 0.056 | 0.884 | 0.142 | 0.112 | 0.035 |
| clinical_trial_matching | claude-code | claude-opus-4-7 | medium | 1 | 10 | 438.23 | 0.883 | 0.105 | 2.000 | 0.200 | 0.422 | 0.542 | 0.161 | 0.747 | 0.158 | 0.452 | 0.168 |
| clinical_trial_matching | claude-code | claude-sonnet-4-6 | medium | 1 | 10 | 1066.02 | 0.817 | 0.153 | 1.000 | 0.100 | 0.316 | 0.423 | 0.183 | 0.738 | 0.142 | 0.329 | 0.204 |
| clinical_trial_matching | codex | gpt-5.3-codex | medium | 1 | 10 | 223.01 | 0.586 | 0.270 | 0.000 | 0.000 | 0.000 | 0.109 | 0.086 | 0.870 | 0.185 | 0.062 | 0.053 |

Per-trial metrics (mean ± sample stdev across subtasks): `ndcg_at_10`, `reward`, `f1`, `precision`, `recall`.

Pooled aggregate metrics from the uv-script aggregator (`<run_dir>/result.json → stats.evals.<key>.metrics[0]`; no per-trial variance available): `success`.

### Reproducibility

```bash
# Codex sweep — requires CODEX_AUTH_JSON to be exported before launching.
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name clinical_trial_matching \
  --task-path tasks \
  --harness codex \
  --output-root /mnt/hanoverdev/scratch/qianchuliu/medcli/results/clinical_trial_matching \
  --attempts 1 \
  --reasoning-effort medium \
  --concurrency 2 \
  --no-detailed \
  --metric-to-report ndcg_at_10 \
  --metric-to-report success \
  --metric-to-report reward \
  --metric-to-report f1 \
  --metric-to-report precision \
  --metric-to-report recall \
  --model gpt-5.5 \
  --model gpt-5.4 \
  --model gpt-5.3-codex
```

## ct_abnormality

- Task path: `tasks`
- Generated at: `20260507T184703Z`
- Raw results root: `/mnt/hanoverdev/scratch/qianchuliu/medcli/results/ct_abnormality`
- Source run dirs:
  - `ct_abnormality__claude-code__claude-opus-4-7__20260507T002218Z`
  - `ct_abnormality__claude-code__claude-sonnet-4-6__20260506T235956Z`
  - `ct_abnormality__codex__gpt-5.3-codex__20260506T235029Z`
  - `ct_abnormality__codex__gpt-5.4__20260506T230833Z`
  - `ct_abnormality__codex__gpt-5.5__20260507T001936Z`

### Aggregate Summary

| Task | Harness | Model | Reasoning | Runs | Sample size | Mean total wall time (s) | success | reward | reward_stdev | macro_f1 | micro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ct_abnormality | claude-code | claude-sonnet-4-6 | medium | 1 | 10 | 1551.30 | 1.000 | 0.100 | 0.316 | 0.517 | 0.590 |
| ct_abnormality | codex | gpt-5.3-codex | medium | 1 | 10 | 273.95 | 1.000 | 0.100 | 0.316 | 0.493 | 0.677 |
| ct_abnormality | codex | gpt-5.4 | medium | 1 | 10 | 466.92 | 1.000 | 0.100 | 0.316 | 0.466 | 0.656 |
| ct_abnormality | codex | gpt-5.5 | medium | 1 | 10 | 461.48 | 1.000 | 0.100 | 0.316 | 0.604 | 0.761 |
| ct_abnormality | claude-code | claude-opus-4-7 | medium | 1 | 10 | 763.70 | 0.000 | 0.000 | 0.000 | 0.511 | 0.588 |

Per-trial metrics (mean ± sample stdev across subtasks): `reward`.

Pooled aggregate metrics from the uv-script aggregator (`<run_dir>/result.json → stats.evals.<key>.metrics[0]`; no per-trial variance available): `success`, `macro_f1`, `micro_f1`.

### Reproducibility

```bash
uv run python scripts/run_harbor_baselines_multitask.py \
  --task-name ct_abnormality \
  --task-path tasks \
  --harness codex \
  --output-root /mnt/hanoverdev/scratch/qianchuliu/medcli/results/ct_abnormality \
  --attempts 1 \
  --reasoning-effort medium \
  --concurrency 2 \
  --no-detailed \
  --metric-to-report success \
  --metric-to-report reward \
  --metric-to-report macro_f1 \
  --metric-to-report micro_f1 \
  --model gpt-5.4 \
  --model gpt-5.3-codex \
  --model gpt-5.5 \
  --model claude-opus-4-7 \
  --model claude-sonnet-4-6
```