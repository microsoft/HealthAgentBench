"""Score an EHRSHOT submission against the published count+gbm baseline.

This module is the canonical scoring routine for our Harbor verifier. It
mirrors the metric and split logic of the upstream EHRSHOT evaluator
(``ehrshot/7_eval_finetune.py`` :: ``calc_metrics`` and
``get_patient_splits_by_idx``) so an AUROC computed here is directly
comparable to the published value in
``EHRSHOT_ASSETS/results/<task>/all_results.csv``.

Key alignment points with upstream:

  * **Score on the TEST split.** The number in ``all_results.csv``'s
    ``value`` column is the test-set score (upstream's
    ``scores[metric]['score']`` is ``test_score``).
  * **Lab tasks** (``lab_*``) binarize via ``value >= 1`` (upstream's
    ``convert_multiclass_to_binary_labels(threshold=1)``).
  * **CheXpert** unpacks the integer ``value`` as a 14-bit bitmask
    (upstream's ``process_chexpert_labels``); each of the 14 subtasks gets
    its own AUROC, and we report the mean across the 14.
  * **AUROC** uses ``sklearn.metrics.roc_auc_score`` with default args.
    AUPRC = ``average_precision_score``; Brier = ``brier_score_loss``.

What the bundle does NOT ship: per-patient probabilities from the
count+gbm baseline. Only the aggregate AUROC/AUPRC/Brier is published.
That's why this script scores **the agent's predictions** against the
test labels and compares the resulting AUROC to the published aggregate.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)


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


@dataclass
class TaskResult:
    task_id: str
    auroc: float
    auprc: float
    brier: float
    n_test: int
    baseline_auroc: float | None
    passed: bool | None
    per_subtask: dict[str, float] | None = None


# ---------------------------------------------------------------------------
# Label loading + binarization (mirrors upstream ehrshot/utils.py)
# ---------------------------------------------------------------------------


def load_test_labels_pre_sliced(test_labels_csv: Path, task_id: str) -> pd.DataFrame:
    """Load already-sliced test_labels.csv (written by stage_data.py).

    Schema:
      binary tasks: patient_id, prediction_time, label
      chexpert:     patient_id, prediction_time, <14 named subtask cols>
    """
    df = pd.read_csv(test_labels_csv)
    df["prediction_time"] = pd.to_datetime(df["prediction_time"])
    return df.reset_index(drop=True)


def load_test_labels(
    labeled_patients_csv: Path,
    splits_csv: Path,
    task_id: str,
) -> pd.DataFrame:
    """Return the test-split rows of labeled_patients.csv with binarized labels.

    For binary tasks (``guo_*``, ``new_*``, ``lab_*``) the returned frame has
    columns ``[patient_id, prediction_time, label]`` (label in {0, 1}).
    For ``chexpert`` it has ``[patient_id, prediction_time, <14 subtask cols>]``.
    """
    labels = pd.read_csv(labeled_patients_csv)
    splits = pd.read_csv(splits_csv)
    test_pids = set(splits.loc[splits["split"] == "test", "omop_person_id"].tolist())
    df = labels[labels["patient_id"].isin(test_pids)].copy()
    df["prediction_time"] = pd.to_datetime(df["prediction_time"])

    if task_id == "chexpert":
        # value is a 14-bit bitmask packed as int. Bit i = CHEXPERT_LABELS[i].
        bits = df["value"].astype(int).map(lambda v: format(v, "014b"))
        for i, name in enumerate(CHEXPERT_LABELS):
            df[name] = bits.map(lambda b, i=i: int(b[i]))
        return df[["patient_id", "prediction_time", *CHEXPERT_LABELS]].reset_index(drop=True)

    if task_id.startswith("lab_"):
        # value is a 0..3 severity int; binarize at >=1 (upstream's threshold=1).
        df["label"] = (df["value"].astype(int) >= 1).astype(int)
    else:
        # guo_* and new_* tasks: value is already bool/0-1.
        df["label"] = df["value"].astype(str).str.lower().map(
            {"true": 1, "false": 0, "1": 1, "0": 0}
        ).astype("Int64")
        if df["label"].isna().any():
            df["label"] = df["value"].astype(int)
        df["label"] = df["label"].astype(int)

    return df[["patient_id", "prediction_time", "label"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Predictions loading + alignment
# ---------------------------------------------------------------------------


def load_predictions(predictions_csv: Path, task_id: str) -> pd.DataFrame:
    """Load the agent's submission. Schema:
       binary tasks: patient_id, prediction_time, probability
       chexpert:     patient_id, prediction_time, <14 subtask columns>
    """
    df = pd.read_csv(predictions_csv)
    df["prediction_time"] = pd.to_datetime(df["prediction_time"])
    return df


def align(labels: pd.DataFrame, preds: pd.DataFrame) -> pd.DataFrame:
    """Inner-join labels and preds on (patient_id, prediction_time).

    Raises if any test row is missing a prediction.
    """
    merged = labels.merge(
        preds,
        on=["patient_id", "prediction_time"],
        how="left",
        suffixes=("_label", "_pred"),
    )
    missing = merged.isna().any(axis=1).sum()
    if missing:
        raise ValueError(
            f"submission is missing predictions for {missing} test rows "
            f"(out of {len(labels)})"
        )
    return merged


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def _binary_metrics(y_true: np.ndarray, y_proba: np.ndarray) -> dict[str, float]:
    return {
        "auroc": float(roc_auc_score(y_true, y_proba)),
        "auprc": float(average_precision_score(y_true, y_proba)),
        "brier": float(brier_score_loss(y_true, y_proba)),
    }


def score_binary_task(labels: pd.DataFrame, preds: pd.DataFrame) -> dict[str, float]:
    merged = align(labels, preds)
    return _binary_metrics(
        merged["label"].to_numpy().astype(int),
        merged["probability"].to_numpy().astype(float),
    )


def score_chexpert(labels: pd.DataFrame, preds: pd.DataFrame) -> tuple[dict[str, float], dict[str, float]]:
    """Returns (mean metrics across 14 subtasks, per-subtask AUROC dict)."""
    merged = align(labels, preds)
    per_subtask_auroc: dict[str, float] = {}
    aurocs, auprcs, briers = [], [], []
    for name in CHEXPERT_LABELS:
        # Submission columns: same names as CHEXPERT_LABELS (probabilities).
        # After merge, label cols and pred cols collide on the same name, so
        # pandas suffix-rules give us ``_label`` / ``_pred`` variants. Use
        # the suffixed forms when present, otherwise fall back to the raw
        # name (covers the unusual case where one side has no collision).
        label_col = f"{name}_label" if f"{name}_label" in merged.columns else name
        proba_col = f"{name}_pred" if f"{name}_pred" in merged.columns else name
        y_true = merged[label_col].to_numpy().astype(int)
        y_proba = merged[proba_col].to_numpy().astype(float)
        m = _binary_metrics(y_true, y_proba)
        per_subtask_auroc[name] = m["auroc"]
        aurocs.append(m["auroc"])
        auprcs.append(m["auprc"])
        briers.append(m["brier"])
    return (
        {
            "auroc": float(np.mean(aurocs)),
            "auprc": float(np.mean(auprcs)),
            "brier": float(np.mean(briers)),
        },
        per_subtask_auroc,
    )


# ---------------------------------------------------------------------------
# Published baseline
# ---------------------------------------------------------------------------


def read_published_count_gbm_auroc(results_csv: Path) -> float | None:
    """Read EHRSHOT's published count+gbm AUROC at k=-1 from all_results.csv.

    For chexpert this averages the 14 subtask AUROCs. For binary tasks there
    is exactly one matching row.
    """
    if not results_csv.is_file():
        return None
    aurocs: list[float] = []
    with results_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                if (
                    row.get("model") == "count"
                    and row.get("head") == "gbm"
                    and row.get("score") == "auroc"
                    and int(row.get("k", "0")) == -1
                ):
                    aurocs.append(float(row["value"]))
            except (KeyError, ValueError, TypeError):
                continue
    return statistics.mean(aurocs) if aurocs else None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def score_submission(
    submission_path: Path,
    test_labels_path: Path,
    task_id: str,
    baseline_auroc: float | None = None,
) -> TaskResult:
    """Verifier-side entry point. Both files are pre-sliced (no bundle needed)."""
    labels = load_test_labels_pre_sliced(test_labels_path, task_id)
    preds = load_predictions(submission_path, task_id)
    if task_id == "chexpert":
        agg, per_subtask = score_chexpert(labels, preds)
        passed = (agg["auroc"] > baseline_auroc) if baseline_auroc is not None else None
        return TaskResult(
            task_id=task_id, auroc=agg["auroc"], auprc=agg["auprc"], brier=agg["brier"],
            n_test=len(labels), baseline_auroc=baseline_auroc, passed=passed,
            per_subtask=per_subtask,
        )
    m = score_binary_task(labels, preds)
    passed = (m["auroc"] > baseline_auroc) if baseline_auroc is not None else None
    return TaskResult(
        task_id=task_id, auroc=m["auroc"], auprc=m["auprc"], brier=m["brier"],
        n_test=len(labels), baseline_auroc=baseline_auroc, passed=passed,
    )


def evaluate(
    predictions_csv: Path,
    assets_dir: Path,
    task_id: str,
) -> TaskResult:
    """Score predictions for one task. ``assets_dir`` points at EHRSHOT_ASSETS/."""
    labeled_patients_csv = assets_dir / "benchmark" / task_id / "labeled_patients.csv"
    splits_csv = assets_dir / "splits" / "person_id_map.csv"
    results_csv = assets_dir / "results" / task_id / "all_results.csv"

    labels = load_test_labels(labeled_patients_csv, splits_csv, task_id)
    preds = load_predictions(predictions_csv, task_id)
    baseline = read_published_count_gbm_auroc(results_csv)

    if task_id == "chexpert":
        agg, per_subtask = score_chexpert(labels, preds)
        passed = (agg["auroc"] > baseline) if baseline is not None else None
        return TaskResult(
            task_id=task_id,
            auroc=agg["auroc"],
            auprc=agg["auprc"],
            brier=agg["brier"],
            n_test=len(labels),
            baseline_auroc=baseline,
            passed=passed,
            per_subtask=per_subtask,
        )

    m = score_binary_task(labels, preds)
    passed = (m["auroc"] > baseline) if baseline is not None else None
    return TaskResult(
        task_id=task_id,
        auroc=m["auroc"],
        auprc=m["auprc"],
        brier=m["brier"],
        n_test=len(labels),
        baseline_auroc=baseline,
        passed=passed,
    )


def _result_to_payload(r: TaskResult) -> dict:
    payload = {
        "task_id": r.task_id,
        "reward": r.auroc,
        "auroc": r.auroc,
        "auprc": r.auprc,
        "brier": r.brier,
        "n_test": r.n_test,
        "baseline_auroc": r.baseline_auroc,
        "passed": r.passed,
    }
    if r.per_subtask is not None:
        payload["per_subtask_auroc"] = r.per_subtask
    return payload


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--assets-dir", type=Path, required=True,
                   help="Path to EHRSHOT_ASSETS/ (the extracted bundle).")
    p.add_argument("--task-id", type=str, required=True)
    p.add_argument("--out", type=Path, default=None,
                   help="If set, write metrics JSON here.")
    args = p.parse_args()

    result = evaluate(args.predictions, args.assets_dir, args.task_id)
    payload = _result_to_payload(result)
    text = json.dumps(payload, indent=2)
    print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
