# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "f1chexbert",
#   "transformers<5",
#   "scikit-learn<1.8",
#   "torch",
#   "numpy",
# ]
# ///
"""Validate that pooled-from-per-sample-labels F1 matches f1chexbert's F1.

Design check: we want to compute CheXbert labels *per sample* (e.g., in the
verifier container, or on the host for each trial) and then aggregate those
label vectors in the aggregator using sklearn. This script proves that the
pooled math is mathematically identical to running f1chexbert end-to-end on
the same list of (prediction, reference) pairs.

Usage:
    uv run scripts/mimic_report_gen/test_aggregation.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, classification_report


# Mock radiology reports (pred, ref) tuples. Deliberately varied so CheXbert
# picks up different labels across samples.
MOCK_SAMPLES = [
    (
        "FINDINGS: Small left pleural effusion. Mild pulmonary edema. No pneumothorax.\n"
        "IMPRESSION: Small left pleural effusion with mild pulmonary edema.",
        "FINDINGS: Moderate pleural effusion on the left side. No edema. No pneumothorax.\n"
        "IMPRESSION: Moderate left pleural effusion.",
    ),
    (
        "FINDINGS: Cardiomegaly with pulmonary edema. No focal consolidation.\n"
        "IMPRESSION: Cardiomegaly and mild pulmonary edema.",
        "FINDINGS: Mild cardiomegaly. Trace pulmonary edema. No pneumothorax.\n"
        "IMPRESSION: Mild cardiomegaly and trace pulmonary edema.",
    ),
    (
        "FINDINGS: No acute cardiopulmonary process. Lungs clear.\n"
        "IMPRESSION: No acute findings.",
        "FINDINGS: Lungs clear. No acute findings.\nIMPRESSION: No acute cardiopulmonary process.",
    ),
    (
        "FINDINGS: Right lower lobe consolidation concerning for pneumonia. No effusion.\n"
        "IMPRESSION: Right lower lobe pneumonia.",
        "FINDINGS: Right lower lobe opacity, suspicious for consolidation.\n"
        "IMPRESSION: Possible right lower lobe pneumonia.",
    ),
    (
        "FINDINGS: Bibasilar atelectasis. No pleural effusion.\n"
        "IMPRESSION: Bibasilar atelectasis.",
        "FINDINGS: Fractured inferior sternotomy wire. Stable sternotomy changes.\n"
        "IMPRESSION: Stable postoperative changes with fractured wire.",
    ),
]


def _ensure_weights() -> None:
    """Place CheXbert weights at the path f1chexbert expects."""
    from appdirs import user_cache_dir

    cache_dir = user_cache_dir("chexbert")
    target = os.path.join(cache_dir, "chexbert.pth")
    if os.path.exists(target):
        return
    os.makedirs(cache_dir, exist_ok=True)
    from huggingface_hub import hf_hub_download

    source = hf_hub_download(
        repo_id="StanfordAIMI/RRG_scorers",
        filename="chexbert.pth",
        cache_dir=cache_dir,
    )
    try:
        os.symlink(source, target)
    except OSError:
        import shutil
        shutil.copy2(source, target)


def _load_labeler():
    _ensure_weights()
    import torch
    from f1chexbert import F1CheXbert

    device = "cuda" if torch.cuda.is_available() else "cpu"
    return F1CheXbert(device=device)


def _label_per_sample(labeler, reports: list[str]) -> np.ndarray:
    """Return (N, 14) label matrix by calling F1CheXbert.get_label() per report."""
    rows = [labeler.get_label(text.strip()) for text in reports]
    return np.asarray(rows, dtype=int)


def _aggregated_metrics(
    labeler, ref_labels: np.ndarray, hyp_labels: np.ndarray
) -> dict:
    """Compute F1+accuracy from pooled label matrices using sklearn directly.

    This mirrors the last several lines of `F1CheXbert.forward()` exactly:
      - classification_report on 14-label matrices for f1_14
      - classification_report on 5-label subset for f1_5
      - accuracy_score on 5-label subset (subset accuracy)
    """
    target_names_14 = list(labeler.target_names)
    target_names_5 = list(labeler.target_names_5)
    idx_5 = labeler.target_names_5_index

    ref_5 = ref_labels[:, idx_5]
    hyp_5 = hyp_labels[:, idx_5]

    cr_14 = classification_report(
        ref_labels, hyp_labels, target_names=target_names_14, output_dict=True
    )
    cr_5 = classification_report(
        ref_5, hyp_5, target_names=target_names_5, output_dict=True
    )
    acc = accuracy_score(y_true=ref_5, y_pred=hyp_5)
    return {"accuracy": acc, "cr_14": cr_14, "cr_5": cr_5}


def _direct_metrics(labeler, preds: list[str], refs: list[str]) -> dict:
    """Run the whole f1chexbert pipeline end-to-end on raw text."""
    acc, _per_sample_acc, cr_14, cr_5 = labeler(hyps=preds, refs=refs)
    return {"accuracy": acc, "cr_14": cr_14, "cr_5": cr_5}


def _compare(a: dict, b: dict) -> list[str]:
    """Return a list of human-readable diffs between two metric dicts."""
    diffs: list[str] = []
    if not np.isclose(a["accuracy"], b["accuracy"], atol=1e-9):
        diffs.append(f"  accuracy differs: pooled={a['accuracy']} vs direct={b['accuracy']}")
    for key in ("cr_14", "cr_5"):
        for avg in ("micro avg", "macro avg", "samples avg", "weighted avg"):
            if avg not in a[key] or avg not in b[key]:
                continue
            for metric in ("precision", "recall", "f1-score", "support"):
                pa = a[key][avg].get(metric)
                pb = b[key][avg].get(metric)
                if pa is None or pb is None:
                    continue
                if not np.isclose(pa, pb, atol=1e-9):
                    diffs.append(f"  {key}[{avg}][{metric}] differs: pooled={pa} direct={pb}")
    return diffs


def main() -> int:
    print("Loading CheXbert labeler...", flush=True)
    labeler = _load_labeler()

    preds = [p for p, _ in MOCK_SAMPLES]
    refs = [r for _, r in MOCK_SAMPLES]
    print(f"Scoring {len(preds)} samples both ways...", flush=True)

    # Path A: per-sample labels → sklearn aggregation
    ref_labels = _label_per_sample(labeler, refs)
    hyp_labels = _label_per_sample(labeler, preds)
    print("\nPer-sample label vectors (rows=samples, cols=labels):")
    print("  labels:", list(labeler.target_names))
    print("  ref:")
    for row in ref_labels:
        print("   ", list(row))
    print("  hyp:")
    for row in hyp_labels:
        print("   ", list(row))

    pooled = _aggregated_metrics(labeler, ref_labels, hyp_labels)

    # Path B: direct f1chexbert call on raw text
    direct = _direct_metrics(labeler, preds, refs)

    # Show headline numbers
    print("\nHeadline numbers:")
    print(
        f"  accuracy:        pooled={pooled['accuracy']:.6f}  "
        f"direct={direct['accuracy']:.6f}"
    )
    print(
        f"  f1_14 micro:     pooled={pooled['cr_14']['micro avg']['f1-score']:.6f}  "
        f"direct={direct['cr_14']['micro avg']['f1-score']:.6f}"
    )
    print(
        f"  f1_14 macro:     pooled={pooled['cr_14']['macro avg']['f1-score']:.6f}  "
        f"direct={direct['cr_14']['macro avg']['f1-score']:.6f}"
    )
    print(
        f"  f1_5 micro:      pooled={pooled['cr_5']['micro avg']['f1-score']:.6f}  "
        f"direct={direct['cr_5']['micro avg']['f1-score']:.6f}"
    )
    print(
        f"  f1_5 macro:      pooled={pooled['cr_5']['macro avg']['f1-score']:.6f}  "
        f"direct={direct['cr_5']['macro avg']['f1-score']:.6f}"
    )

    diffs = _compare(pooled, direct)
    if diffs:
        print("\n❌ FAIL — pooled aggregation does not match direct f1chexbert:")
        for d in diffs:
            print(d)
        return 1
    print("\n✅ OK — per-sample label aggregation matches f1chexbert end-to-end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
