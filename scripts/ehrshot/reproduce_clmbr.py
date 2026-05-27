"""Reproduce EHRSHOT's published clmbr + lr_lbfgs AUROC for every task.

Mirrors ``ehrshot/7_eval_finetune.py``'s ``run_frozen_feature_evaluation`` for
the ``clmbr + lr_lbfgs`` head at ``k = -1`` (all training data). The CLMBR
features are pre-computed and shipped in ``EHRSHOT_ASSETS/features/
clmbr_features.pkl`` as a 406379 x 768 float16 matrix aligned to every
labeled (patient, prediction_time) row across all 15 tasks.

Upstream's recipe for the lr_lbfgs head:

    scaler = MaxAbsScaler().fit(X_train)
    X_{train,val,test} = scaler.transform(...)
    model = LogisticRegression(solver="lbfgs", penalty="l2", tol=1e-4,
                               max_iter=1000, random_state=0)
    GridSearchCV with PredefinedSplit (train fold = -1, val = 0),
        scoring="roc_auc", refit=False, over LR_PARAMS =
        {"C": [1e-8, 1e-6, 1e-4, 1e-2, 1e-1, 1, 1e2, 1e4], "penalty": ["l2"]}
    best = LR(**best_params).fit(X_train, y_train)   # refit on train only
    y_test_proba = best.predict_proba(X_test)[:, 1]
    auroc = roc_auc_score(y_test, y_test_proba)

We report both the full-test AUROC (matches published) and the auroc_last
subset (one row per patient at their latest prediction_time, matching our
benchmark's chosen test cohort).

Output: ``scripts/ehrshot/assets/baselines_clmbr.csv`` and per-row
predictions under ``scripts/ehrshot/assets/predictions_clmbr/``.
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.preprocessing import MaxAbsScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reproduce_baseline import (  # noqa: E402
    CHEXPERT_LABELS,
    align_features_to_labels,
    load_labels,
    load_split_pids,
    split_indices,
)
from reproduce_all_tasks import (  # noqa: E402
    _first_pred_time_mask,
    _last_pred_time_mask,
    _save_predictions,
    _single_pred_time_mask,
    _safe_metrics,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ASSETS_DIR = REPO_ROOT / "scripts" / "ehrshot" / "assets" / "EHRSHOT_ASSETS"
DEFAULT_OUTPUT = REPO_ROOT / "scripts" / "ehrshot" / "assets" / "baselines_clmbr.csv"
DEFAULT_PRED_DIR = REPO_ROOT / "scripts" / "ehrshot" / "assets" / "predictions_clmbr"

ALL_TASKS = (
    "guo_icu", "guo_los", "guo_readmission",
    "new_acutemi", "new_celiac", "new_hyperlipidemia",
    "new_hypertension", "new_lupus", "new_pancan",
    "lab_anemia", "lab_hyperkalemia", "lab_hypoglycemia",
    "lab_hyponatremia", "lab_thrombocytopenia",
    "chexpert",
)

# Upstream LR_PARAMS from ehrshot/utils.py
LR_PARAMS = {
    "C": [1e-8, 1e-6, 1e-4, 1e-2, 1e-1, 1, 1e2, 1e4],
    "penalty": ["l2"],
}


def _log(msg: str) -> None:
    print(f"[clmbr-sweep] {msg}", file=sys.stderr, flush=True)


def load_clmbr_features(assets_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load clmbr_features.pkl. Returns (matrix, patient_ids, prediction_times).

    The matrix is float16 in the bundle; we keep it that way to halve memory
    until indexing, then upcast to float32 for sklearn.
    """
    import pickle
    with open(assets_dir / "features" / "clmbr_features.pkl", "rb") as f:
        d = pickle.load(f)
    return (
        d["data_matrix"],            # (406379, 768) float16
        d["patient_ids"].astype(np.int64),
        np.asarray(d["labeling_time"]).astype("datetime64[us]"),
    )


def fit_clmbr_lr(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    replicate: int = 0,
    n_jobs: int = 8,
) -> tuple[LogisticRegression, MaxAbsScaler, dict]:
    """Mirror upstream's run_frozen_feature_evaluation for lr_lbfgs."""
    # Shuffle train (matches np.random.seed(replicate))
    rng = np.random.default_rng(replicate)
    perm = rng.permutation(X_train.shape[0])
    X_train = X_train[perm]
    y_train = y_train[perm]

    scaler = MaxAbsScaler().fit(X_train)
    X_train = scaler.transform(X_train)
    X_val = scaler.transform(X_val)

    # PredefinedSplit: train fold = -1, val = 0
    X = np.vstack([X_train, X_val])
    y = np.concatenate([y_train, y_val])
    test_fold = -np.ones(X.shape[0], dtype=int)
    test_fold[X_train.shape[0]:] = 0

    base = LogisticRegression(
        n_jobs=1, penalty="l2", tol=1e-4, solver="lbfgs",
        max_iter=1000, random_state=replicate,
    )
    cv = GridSearchCV(
        base, LR_PARAMS, scoring="roc_auc", n_jobs=n_jobs,
        cv=PredefinedSplit(test_fold), refit=False, verbose=0,
    )
    cv.fit(X, y)
    best = LogisticRegression(
        **cv.best_params_, n_jobs=1, tol=1e-4, solver="lbfgs",
        max_iter=1000, random_state=replicate,
    )
    best.fit(X_train, y_train)
    return best, scaler, cv.best_params_


def _run_binary_task(
    task_id: str,
    feat_matrix: np.ndarray,
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
    X = np.asarray(feat_matrix[feat_idx]).astype(np.float32)
    y = label_values
    splits = split_indices(label_pids, split_pids)
    X_train, X_val, X_test = X[splits["train"]], X[splits["val"]], X[splits["test"]]
    y_train, y_val, y_test = y[splits["train"]], y[splits["val"]], y[splits["test"]]
    test_pids = label_pids[splits["test"]]
    test_times = label_times[splits["test"]]

    _log(f"{task_id}: train={len(y_train)} val={len(y_val)} test={len(y_test)}")
    model, scaler, best_params = fit_clmbr_lr(
        X_train, y_train, X_val, y_val, replicate=0, n_jobs=n_jobs,
    )
    proba = model.predict_proba(scaler.transform(X_test))[:, 1]

    _save_predictions(pred_dir, task_id, test_pids, test_times, y_test, proba)

    auroc_full, auprc_full = _safe_metrics(y_test, proba)
    m_single = _single_pred_time_mask(test_pids)
    m_first = _first_pred_time_mask(test_pids, test_times)
    m_last = _last_pred_time_mask(test_pids, test_times)
    auroc_single, auprc_single = _safe_metrics(y_test[m_single], proba[m_single])
    auroc_first, auprc_first = _safe_metrics(y_test[m_first], proba[m_first])
    auroc_last, auprc_last = _safe_metrics(y_test[m_last], proba[m_last])

    return {
        "task": task_id,
        "train_n": len(y_train), "val_n": len(y_val),
        "test_full_n": len(y_test),
        "test_single_n": int(m_single.sum()),
        "test_first_n": int(m_first.sum()),
        "test_last_n": int(m_last.sum()),
        "prevalence_full": float(y_test.mean()),
        "auroc_full": auroc_full, "auroc_single": auroc_single,
        "auroc_first": auroc_first, "auroc_last": auroc_last,
        "auprc_full": auprc_full, "auprc_single": auprc_single,
        "auprc_first": auprc_first, "auprc_last": auprc_last,
        "best_hparams": json.dumps(best_params),
        "fit_seconds": round(time.time() - t0, 1),
    }


def _run_chexpert(
    feat_matrix: np.ndarray,
    feat_pids: np.ndarray,
    feat_times: np.ndarray,
    assets_dir: Path,
    split_pids: dict[str, set[int]],
    n_jobs: int,
    pred_dir: Path,
) -> dict:
    t0 = time.time()
    label_pids, label_times, raw_values = load_labels(assets_dir, "chexpert")
    bits = np.array(
        [[int(b) for b in format(int(v), "014b")] for v in raw_values],
        dtype=np.int64,
    )
    feat_idx = align_features_to_labels(feat_pids, feat_times, label_pids, label_times)
    X = np.asarray(feat_matrix[feat_idx]).astype(np.float32)
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
    best_params_per: dict[str, dict] = {}
    train_n = val_n = test_n = 0

    for i, sub in enumerate(CHEXPERT_LABELS):
        y = bits[:, i]
        X_train, X_val, X_test = X[splits["train"]], X[splits["val"]], X[splits["test"]]
        y_train, y_val, y_test = y[splits["train"]], y[splits["val"]], y[splits["test"]]
        if i == 0:
            train_n, val_n, test_n = len(y_train), len(y_val), len(y_test)
        if y_test.sum() == 0 or y_test.sum() == len(y_test):
            _log(f"chexpert/{sub}: degenerate, skipping")
            continue
        _log(f"chexpert/{sub}: positives train={int(y_train.sum())}/{len(y_train)}")
        model, scaler, hp = fit_clmbr_lr(X_train, y_train, X_val, y_val, replicate=0, n_jobs=n_jobs)
        proba = model.predict_proba(scaler.transform(X_test))[:, 1]
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

    return {
        "task": "chexpert",
        "train_n": train_n, "val_n": val_n,
        "test_full_n": test_n,
        "test_single_n": int(m_single.sum()),
        "test_first_n": int(m_first.sum()),
        "test_last_n": int(m_last.sum()),
        "prevalence_full": float(bits[splits["test"]].mean()),
        "auroc_full": float(np.mean(aurocs_full)) if aurocs_full else float("nan"),
        "auroc_single": float(np.mean(aurocs_single)) if aurocs_single else float("nan"),
        "auroc_first": float(np.mean(aurocs_first)) if aurocs_first else float("nan"),
        "auroc_last": float(np.mean(aurocs_last)) if aurocs_last else float("nan"),
        "auprc_full": float(np.mean(auprcs_full)) if auprcs_full else float("nan"),
        "auprc_single": float(np.mean(auprcs_single)) if auprcs_single else float("nan"),
        "auprc_first": float(np.mean(auprcs_first)) if auprcs_first else float("nan"),
        "auprc_last": float(np.mean(auprcs_last)) if auprcs_last else float("nan"),
        "best_hparams": json.dumps(best_params_per),
        "fit_seconds": round(time.time() - t0, 1),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--pred-dir", type=Path, default=DEFAULT_PRED_DIR)
    p.add_argument("--n-jobs", type=int, default=8)
    p.add_argument("--tasks", type=str, default=",".join(ALL_TASKS))
    args = p.parse_args()
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]

    _log(f"loading clmbr_features.pkl from {args.assets_dir}/features/")
    t0 = time.time()
    feat_matrix, feat_pids, feat_times = load_clmbr_features(args.assets_dir)
    _log(f"  features: {feat_matrix.shape}, dtype {feat_matrix.dtype} ({time.time()-t0:.0f}s)")

    split_pids = load_split_pids(args.assets_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task", "train_n", "val_n",
        "test_full_n", "test_single_n", "test_first_n", "test_last_n",
        "prevalence_full",
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
                                        args.assets_dir, split_pids, args.n_jobs, args.pred_dir)
                else:
                    row = _run_binary_task(task, feat_matrix, feat_pids, feat_times,
                                           args.assets_dir, split_pids, args.n_jobs, args.pred_dir)
                writer.writerow(row); f.flush()
                _log(f"DONE {task}: AUROC full={row['auroc_full']:.4f} last={row['auroc_last']:.4f} "
                     f"[{row['fit_seconds']:.0f}s]")
            except Exception as e:  # noqa: BLE001
                _log(f"FAILED {task}: {type(e).__name__}: {e}")

    _log(f"done -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
