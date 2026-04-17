# /// script
# requires-python = ">=3.10"
# dependencies = [
#   # scikit-learn 1.8 changed _check_targets internals; we use only the
#   # stable classification_report/accuracy_score APIs, so any 1.x is fine.
#   "scikit-learn",
#   "numpy",
# ]
# ///
"""Harbor uv-script metric: pool per-trial CheXbert labels into F1 + accuracy.

Each per-trial `reward.json` (written by verify_meta_task.py) carries 28
scalar fields encoding two 14-dim CheXbert label vectors — one for the
reference report and one for the prediction:

    chx_ref_enlarged_cardiomediastinum     0 or 1
    chx_ref_cardiomegaly                   0 or 1
    ...
    chx_pred_no_finding                    0 or 1

Harbor concatenates every trial's reward.json into `rewards.jsonl` and passes
it here. We stack the vectors into two (N, 14) matrices and run sklearn's
`classification_report` + `accuracy_score` — mathematically identical to
running f1chexbert end-to-end on the same text (see test_aggregation.py).

Plus the scalar averages BLEU / ROUGE-L / fill_rate from each trial.

Usage (invoked automatically by Harbor via the `metrics` config):
    uv run scripts/mimic_report_gen/aggregate_metric.py \
        -i rewards.jsonl -o metric.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Full 14-label CheXpert ordering used by f1chexbert.target_names.
CHEXBERT_LABELS: tuple[str, ...] = (
    "Enlarged Cardiomediastinum",
    "Cardiomegaly",
    "Lung Opacity",
    "Lung Lesion",
    "Edema",
    "Consolidation",
    "Pneumonia",
    "Atelectasis",
    "Pneumothorax",
    "Pleural Effusion",
    "Pleural Other",
    "Fracture",
    "Support Devices",
    "No Finding",
)

# The 5 clinically important labels f1chexbert reports separately.
CHEXBERT_LABELS_5: tuple[str, ...] = (
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Pleural Effusion",
)
CHEXBERT_IDX_5: tuple[int, ...] = tuple(
    CHEXBERT_LABELS.index(name) for name in CHEXBERT_LABELS_5
)


def _slug(label: str) -> str:
    return label.replace(" ", "_").lower()


def _field_name(role: str, label: str) -> str:
    """Mirror chexbert_labeler.label_field_name so both sides agree on keys."""
    return f"chx_{role}_{_slug(label)}"


def _load_trials(input_path: Path) -> list[dict]:
    trials: list[dict] = []
    for line in input_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj is not None:
            trials.append(obj)
    return trials


def _extract_label_matrices(trials: list[dict]) -> tuple["np.ndarray", "np.ndarray", int]:
    """Stack per-trial CheXbert label vectors into (N, 14) matrices.

    Trials that don't carry a full set of chx_* scalars are silently skipped;
    the caller checks the returned count before running sklearn.
    """
    import numpy as np

    refs: list[list[int]] = []
    hyps: list[list[int]] = []
    for t in trials:
        ref_vec: list[int] = []
        hyp_vec: list[int] = []
        complete = True
        for label in CHEXBERT_LABELS:
            r_key = _field_name("ref", label)
            p_key = _field_name("pred", label)
            if r_key not in t or p_key not in t:
                complete = False
                break
            ref_vec.append(int(t[r_key]))
            hyp_vec.append(int(t[p_key]))
        if complete:
            refs.append(ref_vec)
            hyps.append(hyp_vec)
    if not refs:
        return np.empty((0, 14), dtype=int), np.empty((0, 14), dtype=int), 0
    return (
        np.asarray(refs, dtype=int),
        np.asarray(hyps, dtype=int),
        len(refs),
    )


def _pooled_chexbert_metrics(refs: "np.ndarray", hyps: "np.ndarray") -> dict:
    """Run sklearn classification_report + accuracy_score on the pooled labels.

    Returns a FLAT dict keyed as ``chexbert_<group>_<stat>`` so downstream
    callers can look a metric up by name without walking a nested tree:

        chexbert_accuracy
        chexbert_n_pairs
        chexbert_f1_14_micro_f1  / _macro_f1  / _samples_f1
        chexbert_f1_5_micro_f1   / _macro_f1  / _samples_f1
    """
    from sklearn.metrics import accuracy_score, classification_report

    refs_5 = refs[:, CHEXBERT_IDX_5]
    hyps_5 = hyps[:, CHEXBERT_IDX_5]

    cr_14 = classification_report(
        refs,
        hyps,
        target_names=list(CHEXBERT_LABELS),
        output_dict=True,
        zero_division=0,
    )
    cr_5 = classification_report(
        refs_5,
        hyps_5,
        target_names=list(CHEXBERT_LABELS_5),
        output_dict=True,
        zero_division=0,
    )
    accuracy = accuracy_score(y_true=refs_5, y_pred=hyps_5)

    def _f1_pct(cr: dict, key: str) -> float:
        return round(100.0 * cr.get(key, {}).get("f1-score", 0.0), 2)

    return {
        "chexbert_accuracy": round(100.0 * accuracy, 2),
        "chexbert_n_pairs": int(refs.shape[0]),
        "chexbert_f1_14_micro_f1": _f1_pct(cr_14, "micro avg"),
        "chexbert_f1_14_macro_f1": _f1_pct(cr_14, "macro avg"),
        "chexbert_f1_14_samples_f1": _f1_pct(cr_14, "samples avg"),
        "chexbert_f1_5_micro_f1": _f1_pct(cr_5, "micro avg"),
        "chexbert_f1_5_macro_f1": _f1_pct(cr_5, "macro avg"),
        "chexbert_f1_5_samples_f1": _f1_pct(cr_5, "samples avg"),
    }


def main(input_path: Path, output_path: Path) -> None:
    trials = _load_trials(input_path)
    if not trials:
        output_path.write_text(json.dumps({"error": "no rewards"}))
        return

    total = sum(int(t.get("total", 0)) for t in trials)
    filled = sum(int(t.get("filled", 0)) for t in trials)
    # Weight each trial's average by its `total` so the aggregate is a proper
    # sample-weighted mean (each trial may internally cover >1 task).
    avg_bleu = (
        sum(float(t.get("avg_bleu", 0.0)) * int(t.get("total", 0)) for t in trials)
        / total
        if total
        else 0.0
    )
    avg_rouge_l = (
        sum(float(t.get("avg_rouge_l", 0.0)) * int(t.get("total", 0)) for t in trials)
        / total
        if total
        else 0.0
    )

    chexbert: dict = {}
    chexbert_error: str | None = None
    try:
        refs, hyps, n_labeled = _extract_label_matrices(trials)
        if n_labeled == 0:
            chexbert_error = (
                "no chx_ref_* / chx_pred_* fields found in rewards.jsonl — "
                "did the verifier emit CheXbert labels? Check "
                "<trial>/verifier/chexbert_error.txt for per-trial errors."
            )
        else:
            chexbert = _pooled_chexbert_metrics(refs, hyps)
    except Exception as e:
        chexbert_error = f"{type(e).__name__}: {e}"

    # All keys are kept flat (no nested "chexbert": {...}) so downstream
    # consumers can look a metric up by a single string key like
    # "chexbert_f1_14_macro_f1". This also matches what Harbor serializes
    # cleanly into result.json.stats.evals.<key>.metrics[0].
    result: dict[str, float | int | str] = {
        "num_trials": len(trials),
        "total_tasks": total,
        "filled_tasks": filled,
        "fill_rate": round(filled / total, 4) if total else 0.0,
        "avg_bleu": round(avg_bleu, 4),
        "avg_rouge_l": round(avg_rouge_l, 4),
    }
    result.update(chexbert)
    if chexbert_error:
        result["chexbert_error"] = chexbert_error

    output_path.write_text(json.dumps(result, indent=2))

    # Summary to stderr so Harbor surfaces it in job output.
    print(f"\n{'='*52}", file=sys.stderr)
    print(
        f" MIMIC-CXR Report Gen Aggregate "
        f"({len(trials)} trials, {total} tasks)",
        file=sys.stderr,
    )
    print(f"  Fill rate:    {result['fill_rate']:.1%}", file=sys.stderr)
    print(f"  Avg BLEU:     {result['avg_bleu']:.4f}", file=sys.stderr)
    print(f"  Avg ROUGE-L:  {result['avg_rouge_l']:.4f}", file=sys.stderr)
    if chexbert:
        print(
            f"  CheXbert F1-14 micro:  {chexbert['chexbert_f1_14_micro_f1']}%  "
            f"(macro {chexbert['chexbert_f1_14_macro_f1']}%, "
            f"samples {chexbert['chexbert_f1_14_samples_f1']}%)",
            file=sys.stderr,
        )
        print(
            f"  CheXbert F1-5  micro:  {chexbert['chexbert_f1_5_micro_f1']}%  "
            f"(macro {chexbert['chexbert_f1_5_macro_f1']}%, "
            f"samples {chexbert['chexbert_f1_5_samples_f1']}%)",
            file=sys.stderr,
        )
        print(
            f"  Accuracy (5-label):    {chexbert['chexbert_accuracy']}%  "
            f"(pooled over {chexbert['chexbert_n_pairs']} samples)",
            file=sys.stderr,
        )
    elif chexbert_error:
        print(f"  CheXbert SKIPPED: {chexbert_error}", file=sys.stderr)
    print(f"{'='*52}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
