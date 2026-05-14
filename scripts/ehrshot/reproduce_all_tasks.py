"""Run the count+gbm baseline for every EHRSHOT task and record AUROC on
both the full test split and the single-prediction-time-per-patient subset.

Train + val are unchanged; only the test cohort is filtered. For chexpert the
subset filter is applied to (patient, prediction_time) rows; each of the 14
subtasks is fit separately and the mean AUROC is reported.

Loads ``count_features.pkl`` once and reuses the matrix across all tasks
(saves ~30s per task setup). With n_jobs=16 on 128 cores, the full sweep
runs in ~2 hours; the lab_* and chexpert tasks dominate.

Output: ``scripts/ehrshot/assets/baselines.csv`` with columns:
  task, train_n, val_n, test_full_n, test_subset_n, prevalence_full,
  prevalence_subset, auroc_full, auroc_subset, auprc_full, auprc_subset,
  best_hparams, fit_seconds.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reproduce_baseline import (  # noqa: E402
    CHEXPERT_LABELS,
    XGB_PARAMS,
    align_features_to_labels,
    fit_count_gbm,
    load_count_features,
    load_labels,
    load_split_pids,
    split_indices,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ASSETS_DIR = REPO_ROOT / "scripts" / "ehrshot" / "assets" / "EHRSHOT_ASSETS"
DEFAULT_OUTPUT = REPO_ROOT / "scripts" / "ehrshot" / "assets" / "baselines.csv"

ALL_TASKS = (
    # Small (~2-3k train rows each)
    "guo_icu", "guo_los", "guo_readmission",
    "new_acutemi", "new_celiac", "new_hyperlipidemia",
    "new_hypertension", "new_lupus", "new_pancan",
    # Large (~50-120k train rows)
    "lab_anemia", "lab_hyperkalemia", "lab_hypoglycemia",
    "lab_hyponatremia", "lab_thrombocytopenia",
    # Multilabel
    "chexpert",
)


def _log(msg: str) -> None:
    print(f"[sweep] {msg}", file=sys.stderr, flush=True)


def _single_pred_time_mask(test_pids: np.ndarray) -> np.ndarray:
    """Return a boolean mask over test rows: True iff the patient has exactly
    ONE row in the test split. For multi-row patients all their rows are False.
    """
    counts = pd.Series(test_pids).value_counts()
    keep = set(counts[counts == 1].index.tolist())
    return np.array([int(p) in keep for p in test_pids], dtype=bool)


def _first_pred_time_mask(test_pids: np.ndarray, test_times: np.ndarray) -> np.ndarray:
    """One row per patient: their EARLIEST prediction_time in the test split."""
    df = pd.DataFrame({"i": np.arange(len(test_pids)), "pid": test_pids, "t": test_times})
    keep_idx = set(df.sort_values("t").drop_duplicates("pid", keep="first")["i"].tolist())
    return np.array([i in keep_idx for i in range(len(test_pids))], dtype=bool)


def _last_pred_time_mask(test_pids: np.ndarray, test_times: np.ndarray) -> np.ndarray:
    """One row per patient: their LATEST prediction_time in the test split."""
    df = pd.DataFrame({"i": np.arange(len(test_pids)), "pid": test_pids, "t": test_times})
    keep_idx = set(df.sort_values("t").drop_duplicates("pid", keep="last")["i"].tolist())
    return np.array([i in keep_idx for i in range(len(test_pids))], dtype=bool)


def _safe_metrics(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    if y.sum() == 0 or y.sum() == len(y):
        return float("nan"), float("nan")
    return (
        float(roc_auc_score(y, p)),
        float(average_precision_score(y, p)),
    )


def _save_predictions(
    out_dir: Path,
    task_id: str,
    test_pids: np.ndarray,
    test_times: np.ndarray,
    y_test: np.ndarray,
    proba: np.ndarray,
    sub_task: str | None = None,
) -> None:
    """Write per-row predictions for a task (or chexpert subtask) to disk.
    Useful for re-evaluating on alternative test subsets without retraining.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{task_id}.csv" if sub_task is None else f"{task_id}__{sub_task.replace(' ', '_')}.csv"
    df = pd.DataFrame({
        "patient_id": test_pids,
        "prediction_time": test_times,
        "label": y_test,
        "probability": proba,
    })
    df.to_csv(out_dir / fname, index=False)


def _run_binary_task(
    task_id: str,
    feat_matrix,
    feat_pids: np.ndarray,
    feat_times: np.ndarray,
    assets_dir: Path,
    split_pids: dict[str, set[int]],
    n_jobs: int,
    pred_dir: Path,
) -> dict:
    t0 = time.time()
    label_pids, label_times, label_values = load_labels(assets_dir, task_id)

    if task_id.startswith("lab_"):
        label_values = (label_values >= 1).astype(int)

    feat_idx = align_features_to_labels(feat_pids, feat_times, label_pids, label_times)
    X = feat_matrix[feat_idx]
    y = label_values
    splits = split_indices(label_pids, split_pids)

    X_train, X_val, X_test = X[splits["train"]], X[splits["val"]], X[splits["test"]]
    y_train, y_val, y_test = y[splits["train"]], y[splits["val"]], y[splits["test"]]
    test_pids = label_pids[splits["test"]]
    test_times = label_times[splits["test"]]

    _log(f"{task_id}: train={len(y_train)} val={len(y_val)} test={len(y_test)}")
    model, best_params = fit_count_gbm(X_train, y_train, X_val, y_val, replicate=0, n_jobs=n_jobs)
    proba = model.predict_proba(X_test)[:, 1]

    _save_predictions(pred_dir, task_id, test_pids, test_times, y_test, proba)

    # Four test subsets: full / single-row-only / first-per-patient / last-per-patient
    auroc_full, auprc_full = _safe_metrics(y_test, proba)
    m_single = _single_pred_time_mask(test_pids)
    auroc_single, auprc_single = _safe_metrics(y_test[m_single], proba[m_single])
    m_first = _first_pred_time_mask(test_pids, test_times)
    auroc_first, auprc_first = _safe_metrics(y_test[m_first], proba[m_first])
    m_last = _last_pred_time_mask(test_pids, test_times)
    auroc_last, auprc_last = _safe_metrics(y_test[m_last], proba[m_last])

    fit_secs = time.time() - t0
    return {
        "task": task_id,
        "train_n": len(y_train),
        "val_n": len(y_val),
        "test_full_n": len(y_test),
        "test_single_n": int(m_single.sum()),
        "test_first_n": int(m_first.sum()),
        "test_last_n": int(m_last.sum()),
        "prevalence_full": float(y_test.mean()),
        "prevalence_single": float(y_test[m_single].mean()) if m_single.sum() else float("nan"),
        "prevalence_first": float(y_test[m_first].mean()) if m_first.sum() else float("nan"),
        "prevalence_last": float(y_test[m_last].mean()) if m_last.sum() else float("nan"),
        "auroc_full": auroc_full,
        "auroc_single": auroc_single,
        "auroc_first": auroc_first,
        "auroc_last": auroc_last,
        "auprc_full": auprc_full,
        "auprc_single": auprc_single,
        "auprc_first": auprc_first,
        "auprc_last": auprc_last,
        "best_hparams": json.dumps(best_params),
        "fit_seconds": round(fit_secs, 1),
    }


def _run_chexpert(
    feat_matrix,
    feat_pids: np.ndarray,
    feat_times: np.ndarray,
    assets_dir: Path,
    split_pids: dict[str, set[int]],
    n_jobs: int,
    pred_dir: Path,
) -> dict:
    """Fit 14 binary classifiers, one per chexpert subtask. Report mean AUROC
    across the 14 on full test, single-pred-time subset, and first-pred-time-
    per-patient subset. Save per-subtask predictions for later re-evaluation.
    """
    t0 = time.time()
    label_pids, label_times, raw_values = load_labels(assets_dir, "chexpert")
    bits = np.array(
        [[int(b) for b in format(int(v), "014b")] for v in raw_values],
        dtype=np.int64,
    )

    feat_idx = align_features_to_labels(feat_pids, feat_times, label_pids, label_times)
    X = feat_matrix[feat_idx]
    splits = split_indices(label_pids, split_pids)
    test_pids = label_pids[splits["test"]]
    test_times = label_times[splits["test"]]
    m_single = _single_pred_time_mask(test_pids)
    m_first = _first_pred_time_mask(test_pids, test_times)
    m_last = _last_pred_time_mask(test_pids, test_times)

    aurocs_full, auprcs_full = [], []
    aurocs_single, auprcs_single = [], []
    aurocs_first, auprcs_first = [], []
    aurocs_last, auprcs_last = [], []
    train_n, val_n, test_n = 0, 0, 0
    best_params_per: dict[str, dict] = {}

    for i, sub in enumerate(CHEXPERT_LABELS):
        y = bits[:, i]
        X_train, X_val, X_test = X[splits["train"]], X[splits["val"]], X[splits["test"]]
        y_train, y_val, y_test = y[splits["train"]], y[splits["val"]], y[splits["test"]]
        if i == 0:
            train_n, val_n, test_n = len(y_train), len(y_val), len(y_test)
        if y_test.sum() == 0 or y_test.sum() == len(y_test):
            _log(f"chexpert/{sub}: degenerate test labels, skipping")
            continue
        _log(f"chexpert/{sub}: train+={int(y_train.sum())}/{len(y_train)} val+={int(y_val.sum())}/{len(y_val)} test+={int(y_test.sum())}/{len(y_test)}")
        model, hp = fit_count_gbm(X_train, y_train, X_val, y_val, replicate=0, n_jobs=n_jobs)
        proba = model.predict_proba(X_test)[:, 1]
        _save_predictions(pred_dir, "chexpert", test_pids, test_times, y_test, proba, sub_task=sub)

        a, p = _safe_metrics(y_test, proba)
        if not np.isnan(a):
            aurocs_full.append(a); auprcs_full.append(p)
        a, p = _safe_metrics(y_test[m_single], proba[m_single])
        if not np.isnan(a):
            aurocs_single.append(a); auprcs_single.append(p)
        a, p = _safe_metrics(y_test[m_first], proba[m_first])
        if not np.isnan(a):
            aurocs_first.append(a); auprcs_first.append(p)
        a, p = _safe_metrics(y_test[m_last], proba[m_last])
        if not np.isnan(a):
            aurocs_last.append(a); auprcs_last.append(p)
        best_params_per[sub] = hp

    fit_secs = time.time() - t0
    return {
        "task": "chexpert",
        "train_n": train_n,
        "val_n": val_n,
        "test_full_n": test_n,
        "test_single_n": int(m_single.sum()),
        "test_first_n": int(m_first.sum()),
        "test_last_n": int(m_last.sum()),
        "prevalence_full": float(bits[splits["test"]].mean()),
        "prevalence_single": float(bits[splits["test"]][m_single].mean()) if m_single.sum() else float("nan"),
        "prevalence_first": float(bits[splits["test"]][m_first].mean()) if m_first.sum() else float("nan"),
        "prevalence_last": float(bits[splits["test"]][m_last].mean()) if m_last.sum() else float("nan"),
        "auroc_full": float(np.mean(aurocs_full)) if aurocs_full else float("nan"),
        "auroc_single": float(np.mean(aurocs_single)) if aurocs_single else float("nan"),
        "auroc_first": float(np.mean(aurocs_first)) if aurocs_first else float("nan"),
        "auroc_last": float(np.mean(aurocs_last)) if aurocs_last else float("nan"),
        "auprc_full": float(np.mean(auprcs_full)) if auprcs_full else float("nan"),
        "auprc_single": float(np.mean(auprcs_single)) if auprcs_single else float("nan"),
        "auprc_first": float(np.mean(auprcs_first)) if auprcs_first else float("nan"),
        "auprc_last": float(np.mean(auprcs_last)) if auprcs_last else float("nan"),
        "best_hparams": json.dumps(best_params_per),
        "fit_seconds": round(fit_secs, 1),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--n-jobs", type=int, default=16,
                   help="Outer GridSearchCV parallelism (each LGBM stays single-threaded).")
    p.add_argument("--tasks", type=str, default=",".join(ALL_TASKS),
                   help="Comma-separated task list to run.")
    args = p.parse_args()

    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    _log(f"loading count_features.pkl from {args.assets_dir}/features/")
    t0 = time.time()
    feat_matrix, feat_pids, feat_times = load_count_features(args.assets_dir)
    _log(f"  features: {feat_matrix.shape}, {feat_matrix.nnz} nnz ({time.time()-t0:.0f}s)")

    split_pids = load_split_pids(args.assets_dir)

    pred_dir = args.output.parent / "predictions"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task", "train_n", "val_n",
        "test_full_n", "test_single_n", "test_first_n", "test_last_n",
        "prevalence_full", "prevalence_single", "prevalence_first", "prevalence_last",
        "auroc_full", "auroc_single", "auroc_first", "auroc_last",
        "auprc_full", "auprc_single", "auprc_first", "auprc_last",
        "best_hparams", "fit_seconds",
    ]

    write_header = not args.output.exists()
    with args.output.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for task in tasks:
            try:
                if task == "chexpert":
                    row = _run_chexpert(feat_matrix, feat_pids, feat_times,
                                        args.assets_dir, split_pids, args.n_jobs, pred_dir)
                else:
                    row = _run_binary_task(task, feat_matrix, feat_pids, feat_times,
                                           args.assets_dir, split_pids, args.n_jobs, pred_dir)
                writer.writerow(row)
                f.flush()
                _log(f"DONE {task}: AUROC full={row['auroc_full']:.4f} single={row['auroc_single']:.4f} "
                     f"first={row['auroc_first']:.4f} last={row['auroc_last']:.4f} "
                     f"(test {row['test_full_n']}/{row['test_single_n']}/{row['test_first_n']}/{row['test_last_n']}) "
                     f"[{row['fit_seconds']:.0f}s]")
            except Exception as e:  # noqa: BLE001
                _log(f"FAILED {task}: {type(e).__name__}: {e}")

    _log(f"all tasks complete -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
