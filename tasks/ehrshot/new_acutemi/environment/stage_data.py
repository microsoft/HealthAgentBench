"""Per-task data slicer. Runs inside the bootstrap container after the
EHRSHOT bundle has been downloaded to /data/_cache/EHRSHOT_ASSETS/.

Responsibilities:
  1. Read labeled_patients.csv for ``--task-id``.
  2. Apply binarization (lab_* -> >=1, chexpert -> 14-bit bitmask expansion).
  3. Partition rows by patient split (train/val/test) using
     splits/person_id_map.csv.
  4. Write agent-visible artifacts under ``--workspace`` (default
     /workspace/data): train_labels.csv, val_labels.csv, test_examples.csv
     (no labels), and splits/person_id_map.csv.
  5. Optionally write test_labels.csv to ``--private`` (host-side generator
     uses this; the container bootstrap passes --no-private).

Notes:
  * Pre-computed features (count_features.pkl, clmbr_features.pkl) are
    intentionally NOT staged. The agent builds its own features from the
    raw event log mounted at /workspace/data/events.csv.
  * The /data/_cache RO mount is intentionally NOT exposed to ``main``, so
    the agent cannot fall back to reading the original labeled_patients.csv.

Designed to run with only numpy/pandas installed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


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


def _log(msg: str) -> None:
    print(f"[stage] {msg}", file=sys.stderr, flush=True)


def load_labels(assets: Path, task_id: str) -> pd.DataFrame:
    """Return a DataFrame with columns:
       binary tasks: patient_id, prediction_time, label (int 0/1)
       chexpert:     patient_id, prediction_time, <14 named binary cols>
    """
    df = pd.read_csv(assets / "benchmark" / task_id / "labeled_patients.csv")
    df["prediction_time"] = pd.to_datetime(df["prediction_time"])

    if task_id == "chexpert":
        bits = df["value"].astype(int).map(lambda v: format(v, "014b"))
        out = df[["patient_id", "prediction_time"]].copy()
        for i, name in enumerate(CHEXPERT_LABELS):
            out[name] = bits.map(lambda b, i=i: int(b[i]))
        return out.reset_index(drop=True)

    if task_id.startswith("lab_"):
        label = (df["value"].astype(int) >= 1).astype(int)
    else:
        label = df["value"].astype(str).str.lower().map(
            {"true": 1, "false": 0, "1": 1, "0": 0}
        ).astype("Int64")
        if label.isna().any():
            label = df["value"].astype(int)
        label = label.astype(int)
    out = df[["patient_id", "prediction_time"]].copy()
    out["label"] = label.values
    return out.reset_index(drop=True)


def slice_events_for_task(
    assets: Path,
    labels: pd.DataFrame,
    test_subset: str,
    out_path: Path,
) -> int:
    """Read ``EHRSHOT_ASSETS/data/ehrshot.csv`` and write a leak-proof
    per-task events.csv at ``out_path``.

    Filtering rules:
      * train + val patients (in this task) → keep all their events
      * test patients in the chosen subset (one row each, with cutoff
        T = their kept prediction_time):
          - keep events with ``start < T``
          - if the row's ``end`` field is in the future (``end >= T``),
            **blank out only the ``end`` column** before writing. The
            row's existence is legitimate information (e.g. "patient
            is admitted right now"), but the future discharge timestamp
            would leak the label for tasks like ``guo_los``. Blanking
            keeps the event visible while removing the leak surface.
      * any other patient → drop entirely

    Returns the number of rows written.
    """
    train_pids = set(labels.loc[labels["split"] == "train", "patient_id"].astype(int).tolist())
    val_pids = set(labels.loc[labels["split"] == "val", "patient_id"].astype(int).tolist())
    test = labels[labels["split"] == "test"].reset_index(drop=True)
    test = filter_test_subset(test, test_subset)
    t_cap = {
        int(p): pd.Timestamp(t)
        for p, t in zip(test["patient_id"], pd.to_datetime(test["prediction_time"]))
    }
    keep_full = train_pids | val_pids
    keep_capped = set(t_cap.keys())

    src = assets / "data" / "ehrshot.csv"
    _log(f"reading {src} (~3 GB)...")
    events = pd.read_csv(src)
    if events.columns[0].startswith("Unnamed"):
        events = events.drop(columns=[events.columns[0]])
    _log(f"  loaded {len(events):,} event rows")

    pid_int = events["patient_id"].astype(int)
    full_mask = pid_int.isin(keep_full)
    test_mask = pid_int.isin(keep_capped)
    if test_mask.any():
        cap_series = pid_int.map(t_cap)
        starts = pd.to_datetime(events["start"])
        ends = pd.to_datetime(events["end"], errors="coerce")
        start_ok = starts < cap_series
        cap_ok = test_mask & start_ok
        # Blank ``end`` where it would leak a future timestamp (end >= T_cap).
        # The row's existence is legitimate info; only the future end is illegal.
        future_end = cap_ok & ends.notna() & (ends >= cap_series)
        n_blanked = int(future_end.sum())
        if n_blanked:
            events = events.copy()
            events.loc[future_end, "end"] = ""
            _log(f"  blanked {n_blanked} future-end timestamps in test slice")
    else:
        cap_ok = pd.Series(False, index=events.index)
    sliced = events[full_mask | cap_ok]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sliced.to_csv(out_path, index=False)
    _log(
        f"events.csv: {len(sliced):,} rows "
        f"({len(sliced)/max(len(events),1):.1%} of full) -> {out_path}"
    )
    return len(sliced)


def attach_split(labels: pd.DataFrame, splits_csv: Path) -> pd.DataFrame:
    splits = pd.read_csv(splits_csv)
    pid2split = dict(zip(splits["omop_person_id"].astype(int), splits["split"]))
    labels["split"] = labels["patient_id"].astype(int).map(pid2split)
    missing = labels["split"].isna().sum()
    if missing:
        _log(f"WARN: {missing} labeled rows have patients not in person_id_map.csv; dropping")
        labels = labels.dropna(subset=["split"]).reset_index(drop=True)
    return labels


TEST_SUBSETS = ("full", "first", "last", "single")


def filter_test_subset(test: pd.DataFrame, subset: str) -> pd.DataFrame:
    """Subset test rows to one row per patient.

    full:   no filter -- every test row kept
    first:  earliest prediction_time per patient (one row per unique patient)
    last:   latest prediction_time per patient
    single: only patients with exactly ONE test row (drops multi-row patients)
    """
    if subset == "full":
        return test
    if subset == "first":
        return test.sort_values("prediction_time").drop_duplicates("patient_id", keep="first").reset_index(drop=True)
    if subset == "last":
        return test.sort_values("prediction_time").drop_duplicates("patient_id", keep="last").reset_index(drop=True)
    if subset == "single":
        counts = test["patient_id"].value_counts()
        keep = set(counts[counts == 1].index.tolist())
        return test[test["patient_id"].isin(keep)].reset_index(drop=True)
    raise ValueError(f"unknown subset: {subset!r}; expected one of {TEST_SUBSETS}")


def write_partitioned_labels(
    labels: pd.DataFrame,
    workspace: Path,
    private: Path | None,
    is_chexpert: bool,
    test_subset: str = "full",
) -> None:
    """Write train_labels.csv, val_labels.csv (visible) + test_examples.csv
    (visible, no labels). If ``private`` is given, also write
    test_labels.csv there.

    In container-runtime use we pass ``private=None`` -- test labels are
    committed at task-generation time to ``tasks/<task>/tests/test_labels.csv``
    on the host (matching ct_abnormality / clinical_trial_matching). This
    function is also reusable on the host for that generation step.
    """
    workspace.mkdir(parents=True, exist_ok=True)
    label_cols: list[str] = list(CHEXPERT_LABELS) if is_chexpert else ["label"]
    base_cols = ["patient_id", "prediction_time"]

    for split in ("train", "val"):
        sub = labels[labels["split"] == split][base_cols + label_cols]
        sub.to_csv(workspace / f"{split}_labels.csv", index=False)
        _log(f"{split}_labels.csv: {len(sub)} rows -> {workspace / f'{split}_labels.csv'}")

    test = labels[labels["split"] == "test"].reset_index(drop=True)
    test = filter_test_subset(test, test_subset)
    _log(f"test subset '{test_subset}': {len(test)} rows")
    test[base_cols].to_csv(workspace / "test_examples.csv", index=False)
    _log(f"test_examples.csv (no labels): {len(test)} rows -> {workspace}/test_examples.csv")

    if private is not None:
        private.mkdir(parents=True, exist_ok=True)
        test[base_cols + label_cols].to_csv(private / "test_labels.csv", index=False)
        _log(f"test_labels.csv: {len(test)} rows -> {private}/test_labels.csv")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task-id", required=True)
    p.add_argument("--assets", type=Path, default=Path("/data/_cache/EHRSHOT_ASSETS"),
                   help="Path to the extracted EHRSHOT bundle.")
    p.add_argument("--workspace", type=Path, default=Path("/workspace/data"),
                   help="Where to write agent-visible artifacts.")
    p.add_argument("--private", type=Path, default=None,
                   help="If set, also write test_labels.csv here. Used by the host-side "
                        "generator to commit test labels into tasks/<task>/tests/. The "
                        "container bootstrap leaves this unset (--no-private below).")
    p.add_argument("--no-private", dest="private", action="store_const", const=None,
                   help="Explicitly skip writing test_labels.csv (for container use).")
    p.add_argument("--test-subset", choices=TEST_SUBSETS, default="last",
                   help="How to subset the test split: full | first | last | single (default: last).")
    p.add_argument("--skip-events", action="store_true",
                   help="Skip producing the sliced events.csv (debug only).")
    args = p.parse_args()

    assets = args.assets
    if not assets.is_dir():
        _log(f"FATAL: --assets {assets} does not exist")
        return 1

    _log(f"task={args.task_id}")
    labels = load_labels(assets, args.task_id)
    _log(f"loaded {len(labels)} labeled rows")
    labels = attach_split(labels, assets / "splits" / "person_id_map.csv")
    counts = labels["split"].value_counts().to_dict()
    _log(f"splits: train={counts.get('train',0)} val={counts.get('val',0)} test={counts.get('test',0)}")

    args.workspace.mkdir(parents=True, exist_ok=True)
    if args.private is not None:
        args.private.mkdir(parents=True, exist_ok=True)

    write_partitioned_labels(
        labels, args.workspace,
        args.private if args.private is not None else None,
        is_chexpert=(args.task_id == "chexpert"),
        test_subset=args.test_subset,
    )

    # Copy the (small) splits CSV so the agent can verify split assignments.
    splits_dir = args.workspace / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    (splits_dir / "person_id_map.csv").write_text(
        (assets / "splits" / "person_id_map.csv").read_text()
    )

    # Per-task sliced events.csv: leak-proof for the chosen test subset.
    if not args.skip_events:
        slice_events_for_task(
            assets, labels, args.test_subset, args.workspace / "events.csv",
        )

    _log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
