"""Reproduce EHRSHOT's published count+gbm test-AUROC for a task.

Mirrors ``ehrshot/7_eval_finetune.py``'s ``run_frozen_feature_evaluation`` for
the ``count + gbm`` head at ``k = -1`` (all training data). On a successful
run, the reproduced AUROC should match the ``value`` column of
``EHRSHOT_ASSETS/results/<task>/all_results.csv`` (filtered to
``model=count, head=gbm, score=auroc, k=-1``) to within numerical noise.

Usage:

    uv run python scripts/ehrshot/reproduce_baseline.py --task-id guo_icu

By default this points at the in-repo bundle at
``scripts/ehrshot/assets/EHRSHOT_ASSETS/`` (override with ``--assets-dir``).
"""

from __future__ import annotations

import argparse
import csv
import pickle
import statistics
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import scipy.sparse
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, PredefinedSplit


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ASSETS_DIR = REPO_ROOT / "scripts" / "ehrshot" / "assets" / "EHRSHOT_ASSETS"


# Mirrors ehrshot/utils.py XGB_PARAMS exactly. min_child_samples=1 is forced
# unconditionally by run_frozen_feature_evaluation (it overrides the dict in
# place before tuning), so we apply it here too.
XGB_PARAMS = {
    "max_depth": [3, 6, -1],
    "learning_rate": [0.02, 0.1, 0.5],
    "num_leaves": [10, 25, 100],
    "min_child_samples": [1],
}


CHEXPERT_LABELS = (
    "No Finding",
    "Enlarged Cardiomediastinum",
    "Cardiomegaly",
    "Lung Lesion",
    "Lung Opacity",
    "Edema",
    "Consolidation",
    "Pneumonia",
    "Atelectasis",
    "Pneumothorax",
    "Pleural Effusion",
    "Pleural Other",
    "Fracture",
    "Support Devices",
)


def load_count_features(assets_dir: Path) -> tuple[scipy.sparse.csr_matrix, np.ndarray, np.ndarray]:
    """Load count_features.pkl. Tuple is (csr_matrix, patient_ids, _, prediction_times)."""
    with open(assets_dir / "features" / "count_features.pkl", "rb") as f:
        feats = pickle.load(f)
    feature_matrix = feats[0]
    feature_pids = feats[1]
    feature_times = feats[3].astype("datetime64[us]")
    return feature_matrix, feature_pids, feature_times


def load_labels(assets_dir: Path, task_id: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read labeled_patients.csv and return (patient_ids, label_times, label_values).

    For binary tasks (guo_*, new_*) values are coerced to int 0/1.
    For lab_* values are int (0-3) and binarized later by the caller.
    For chexpert values are int bitmasks (preserved; expanded by the caller).
    """
    df = pd.read_csv(assets_dir / "benchmark" / task_id / "labeled_patients.csv")
    df["prediction_time"] = pd.to_datetime(df["prediction_time"])
    pids = df["patient_id"].to_numpy(dtype=np.int64)
    times = df["prediction_time"].to_numpy().astype("datetime64[us]")

    raw = df["value"]
    if task_id == "chexpert" or task_id.startswith("lab_"):
        values = raw.astype(int).to_numpy()
    else:
        values = raw.astype(str).str.lower().map({"true": 1, "false": 0, "1": 1, "0": 0}).astype(int).to_numpy()
    return pids, times, values


def align_features_to_labels(
    feat_pids: np.ndarray,
    feat_times: np.ndarray,
    label_pids: np.ndarray,
    label_times: np.ndarray,
) -> np.ndarray:
    """Return per-label-row indices into the (sorted) feature arrays.

    Mirrors ehrshot/utils.py compute_feature_label_alignment + the surrounding
    lexsort. We:
      1. Lexsort labels by (patient_id, time) — input order isn't guaranteed.
      2. Lexsort features the same way.
      3. For each label row, binary-search the feature side for an exact match.

    Returns indices into the *original* feature matrix (un-permuted).
    """
    # Lexsort: primary key = patient_id, secondary = time
    label_order = np.lexsort((label_times, label_pids))
    feat_order = np.lexsort((feat_times, feat_pids))
    feat_pids_sorted = feat_pids[feat_order]
    feat_times_sorted = feat_times[feat_order]

    label_pids_sorted = label_pids[label_order]
    label_times_sorted = label_times[label_order]

    # Per (pid, time) lookup. Build a dict on the feature side keyed by the
    # int64 cast of (pid, ns_since_epoch). Faster than np.searchsorted on a
    # 2-key lex order at this scale (~400k features).
    feat_keys = np.stack(
        [feat_pids_sorted, feat_times_sorted.astype("datetime64[ns]").astype(np.int64)],
        axis=1,
    )
    label_keys = np.stack(
        [label_pids_sorted, label_times_sorted.astype("datetime64[ns]").astype(np.int64)],
        axis=1,
    )
    # Hash via tuple keys — labels << features in this dataset.
    feat_index = {(int(k[0]), int(k[1])): i for i, k in enumerate(feat_keys)}
    sorted_match = np.empty(len(label_keys), dtype=np.int64)
    missing = 0
    for i, k in enumerate(label_keys):
        v = feat_index.get((int(k[0]), int(k[1])))
        if v is None:
            missing += 1
            sorted_match[i] = -1
        else:
            sorted_match[i] = v
    if missing:
        raise RuntimeError(f"{missing} of {len(label_keys)} label rows had no matching feature row")

    # sorted_match maps sorted-label-i -> sorted-feature-j. Convert back to
    # original feature indices and original label order.
    feat_orig_idx = feat_order[sorted_match]            # sorted-label-i -> original-feature
    inv_label_order = np.argsort(label_order)            # original-label-i -> sorted-label-i
    return feat_orig_idx[inv_label_order]


def load_split_pids(assets_dir: Path) -> dict[str, set[int]]:
    df = pd.read_csv(assets_dir / "splits" / "person_id_map.csv")
    return {
        s: set(df.loc[df["split"] == s, "omop_person_id"].astype(int).tolist())
        for s in ("train", "val", "test")
    }


def split_indices(label_pids: np.ndarray, split_pids: dict[str, set[int]]) -> dict[str, np.ndarray]:
    out = {}
    for s, pid_set in split_pids.items():
        mask = np.fromiter((int(p) in pid_set for p in label_pids), dtype=bool, count=len(label_pids))
        out[s] = np.flatnonzero(mask)
    return out


def fit_count_gbm(
    X_train: scipy.sparse.csr_matrix,
    y_train: np.ndarray,
    X_val: scipy.sparse.csr_matrix,
    y_val: np.ndarray,
    replicate: int = 0,
    n_jobs: int = 4,
) -> lgb.LGBMClassifier:
    """Fit count+gbm using GridSearchCV + PredefinedSplit, refit best on train only.

    Mirrors run_frozen_feature_evaluation's gbm branch + tune_hyperparams.
    """
    # Shuffle train (matches np.random.seed(replicate)).
    rng = np.random.default_rng(replicate)
    perm = rng.permutation(X_train.shape[0])
    X_train = X_train[perm]
    y_train = y_train[perm]

    # Stack train+val for PredefinedSplit grid search. Train fold = -1, val = 0.
    X = scipy.sparse.vstack([X_train, X_val])
    y = np.concatenate([y_train, y_val])
    test_fold = -np.ones(X.shape[0], dtype=int)
    test_fold[X_train.shape[0]:] = 0

    print(f"[fit] grid search: {len(XGB_PARAMS['max_depth']) * len(XGB_PARAMS['learning_rate']) * len(XGB_PARAMS['num_leaves'])} configs, "
          f"train={X_train.shape[0]}, val={X_val.shape[0]}, n_jobs={n_jobs}", file=sys.stderr, flush=True)
    t0 = time.time()
    base = lgb.LGBMClassifier(random_state=replicate, verbose=-1, n_jobs=1)
    cv = GridSearchCV(
        base,
        XGB_PARAMS,
        scoring="roc_auc",
        n_jobs=n_jobs,
        cv=PredefinedSplit(test_fold),
        refit=False,
        verbose=3,  # logs each fit's start + completion time + val AUROC
    )
    cv.fit(X, y)
    print(f"[fit] grid search done in {time.time()-t0:.0f}s. best_params={cv.best_params_}", file=sys.stderr, flush=True)
    print(f"[fit] refitting best config on train only...", file=sys.stderr, flush=True)
    t1 = time.time()
    best = lgb.LGBMClassifier(**cv.best_params_, random_state=replicate, verbose=-1, n_jobs=n_jobs)
    # Refit on train only — mirrors tune_hyperparams's "truly k-shot" comment.
    best.fit(X_train, y_train)
    print(f"[fit] refit done in {time.time()-t1:.0f}s", file=sys.stderr, flush=True)
    return best, cv.best_params_


def published_count_gbm_auroc(assets_dir: Path, task_id: str) -> dict[str, float]:
    """Return dict mapping sub_task -> published AUROC at model=count, head=gbm, k=-1."""
    p = assets_dir / "results" / task_id / "all_results.csv"
    out: dict[str, float] = {}
    with p.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                if (
                    row["model"] == "count"
                    and row["head"] == "gbm"
                    and row["score"] == "auroc"
                    and int(row["k"]) == -1
                ):
                    sub = row.get("sub_task") or task_id
                    # Multiple replicates at k=-1 (5 of them, identical data) — average.
                    out.setdefault(sub, []).append(float(row["value"]))
            except (KeyError, ValueError):
                continue
    return {k: statistics.mean(v) for k, v in out.items()}


def reproduce_one(
    task_id: str,
    sub_task: str,
    feature_matrix: scipy.sparse.csr_matrix,
    feat_pids: np.ndarray,
    feat_times: np.ndarray,
    label_pids: np.ndarray,
    label_times: np.ndarray,
    label_values: np.ndarray,
    split_pids: dict[str, set[int]],
    n_jobs: int,
) -> tuple[float, dict, int, int, int]:
    print(f"[align] aligning {len(label_pids)} labels to features...", file=sys.stderr, flush=True)
    t0 = time.time()
    feat_idx = align_features_to_labels(feat_pids, feat_times, label_pids, label_times)
    print(f"[align] done in {time.time()-t0:.0f}s", file=sys.stderr, flush=True)
    X = feature_matrix[feat_idx]
    y = label_values
    splits = split_indices(label_pids, split_pids)

    X_train, X_val, X_test = X[splits["train"]], X[splits["val"]], X[splits["test"]]
    y_train, y_val, y_test = y[splits["train"]], y[splits["val"]], y[splits["test"]]

    if y_test.sum() == 0 or y_test.sum() == len(y_test):
        raise RuntimeError(f"degenerate test labels for {sub_task}: positives={int(y_test.sum())}/{len(y_test)}")

    model, best_params = fit_count_gbm(X_train, y_train, X_val, y_val, replicate=0, n_jobs=n_jobs)
    proba = model.predict_proba(X_test)[:, 1]
    auroc = float(roc_auc_score(y_test, proba))
    return auroc, best_params, len(y_train), len(y_val), len(y_test)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task-id", required=True)
    p.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    p.add_argument("--n-jobs", type=int, default=4)
    args = p.parse_args()

    t0 = time.time()
    print(f"[reproduce] loading count_features.pkl ...", file=sys.stderr)
    feat_matrix, feat_pids, feat_times = load_count_features(args.assets_dir)
    print(f"  features: {feat_matrix.shape}, {feat_matrix.nnz} nnz ({time.time()-t0:.1f}s)", file=sys.stderr)

    label_pids, label_times, label_values = load_labels(args.assets_dir, args.task_id)
    print(f"[reproduce] {args.task_id}: {len(label_pids)} labeled rows", file=sys.stderr)

    split_pids = load_split_pids(args.assets_dir)
    published = published_count_gbm_auroc(args.assets_dir, args.task_id)

    if args.task_id == "chexpert":
        # value is a 14-bit bitmask. Expand to (N, 14) binary array.
        bits = np.array(
            [[int(b) for b in format(int(v), "014b")] for v in label_values],
            dtype=np.int64,
        )
        per_subtask: dict[str, float] = {}
        for i, sub in enumerate(CHEXPERT_LABELS):
            t1 = time.time()
            auroc, hp, n_tr, n_va, n_te = reproduce_one(
                args.task_id, sub, feat_matrix, feat_pids, feat_times,
                label_pids, label_times, bits[:, i], split_pids, args.n_jobs,
            )
            pub = published.get(sub)
            delta = (auroc - pub) if pub is not None else None
            print(
                f"  {sub:32s} reproduced={auroc:.6f}  published={pub if pub is None else f'{pub:.6f}'}"
                f"  Δ={delta if delta is None else f'{delta:+.6f}'}"
                f"  (train={n_tr}/val={n_va}/test={n_te}, {time.time()-t1:.0f}s)"
            )
            per_subtask[sub] = auroc
        mean_repro = float(np.mean(list(per_subtask.values())))
        mean_pub = float(np.mean(list(published.values())))
        print(f"\n  MEAN AUROC across 14 subtasks: reproduced={mean_repro:.6f}  published={mean_pub:.6f}  Δ={mean_repro-mean_pub:+.6f}")
        return 0

    # Binary tasks
    if args.task_id.startswith("lab_"):
        label_values = (label_values >= 1).astype(int)

    auroc, hp, n_tr, n_va, n_te = reproduce_one(
        args.task_id, args.task_id, feat_matrix, feat_pids, feat_times,
        label_pids, label_times, label_values, split_pids, args.n_jobs,
    )
    pub = published.get(args.task_id)
    delta = (auroc - pub) if pub is not None else None
    print(f"\n  task: {args.task_id}")
    print(f"  splits: train={n_tr} val={n_va} test={n_te}")
    print(f"  best hparams: {hp}")
    print(f"  reproduced AUROC: {auroc:.6f}")
    print(f"  published AUROC:  {pub if pub is None else f'{pub:.6f}'}")
    if delta is not None:
        print(f"  Δ:                {delta:+.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
