"""Create leak-resistant inputs for the MSK-CHORD BRCA survival task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import KFold

DATASET_NAME = "mskchord"
COHORT = "brca"
PREDICTION_TASK = "SURV_PROB"
SOURCE_FILENAME = "brca_dx_1st_seq_OS.csv"
NUM_FOLDS = 5
FOLD = 0
SEED = 20

FEATURE_COLUMNS = (
    "AGE",
    "MALE",
    "WHITE",
    "ASIAN",
    "BLACK",
    "SMOKER",
    "ANY_PRIOR_TX",
    "STAGE 1",
    "STAGE 2",
    "STAGE 3",
    "STAGE 4",
    "STAGE_IV_DX",
    "STAGE_I-III_NOPROG",
    "STAGE_I-III_PROG",
    "progressed",
    "DMETS_DX_ADRENAL",
    "DMETS_DX_BONE",
    "DMETS_DX_BRAIN",
    "DMETS_DX_LIVER",
    "DMETS_DX_LUNG",
    "DMETS_DX_LYMPH",
    "DMETS_DX_PLEURA",
    "DMETS_DX_OTHER",
    "Gleason",
    "HAS_Gleason",
    "ADENOCARCINOMA",
    "SQUAMOUS",
    "PDL1",
    "HAS_PDL1",
    "HR",
    "HER2",
    "RECTAL",
    "ASCENDING",
    "CECUM",
    "NONADENOCARCINOMA",
    "MUCINOUS",
    "MSI_OR_dMMR",
    "HAS_MSI_OR_dMMR",
    "MAX_CA15-3",
    "CA15-3",
    "HAS_CA15-3",
    "MAX_CEA",
    "CEA",
    "HAS_CEA",
    "MAX_PSA",
    "PSA",
    "HAS_PSA",
    "MAX_CA19-9",
    "CA19-9",
    "HAS_CA19-9",
    "KRAS",
    "HRAS",
    "RET",
    "MET",
    "GNAQ",
    "PTEN",
    "KIT",
    "EGFR",
    "FGFR1",
    "FGFR2",
    "FGFR3",
    "PDGFRA",
    "ERBB2",
    "TP53",
    "NRAS",
    "NOTCH1",
    "GNA11",
    "CTNNB1",
    "PIK3CA",
    "IDH1",
    "BRAF",
    "ALK",
    "AKT1",
)

_REQUIRED_COLUMNS = {"PATIENT_ID", "entry", "stop", "dead"}
_OUTCOME_COLUMNS = ["sample_id", "observed_time_days", "event_observed"]


def load_cohort(
    source_dir: Path,
) -> tuple[pd.DataFrame, list[str], dict[str, int]]:
    path = source_dir / SOURCE_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"MSK-CHORD cohort file not found: {path}")

    frame = pd.read_csv(path)
    missing = sorted(_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")

    n_source_rows = len(frame)
    frame = frame.drop_duplicates(ignore_index=True)
    n_exact_duplicate_rows_removed = n_source_rows - len(frame)
    patient_ids = frame["PATIENT_ID"].astype(str)
    duplicate_patient_ids = sorted(
        patient_ids[patient_ids.duplicated(keep=False)].unique()
    )
    if duplicate_patient_ids:
        raise ValueError(
            "source contains non-identical rows for PATIENT_ID values: "
            + ", ".join(duplicate_patient_ids)
        )

    frame = frame.copy()
    frame["observed_time_days"] = frame["stop"].astype(float) - frame["entry"].astype(
        float
    )
    frame["event_observed"] = frame["dead"].astype(bool)
    frame = frame[frame["observed_time_days"] >= 0].reset_index(drop=True)
    frame["sample_id"] = frame["PATIENT_ID"].astype(str)

    features = [column for column in FEATURE_COLUMNS if column in frame.columns]
    cohort_flag = f"has_{COHORT}"
    frame[cohort_flag] = 1
    features.append(cohort_flag)
    preprocessing = {
        "n_source_rows": n_source_rows,
        "n_exact_duplicate_rows_removed": n_exact_duplicate_rows_removed,
        "n_rows_after_deduplication": len(frame),
    }
    return frame, features, preprocessing


def split_cohort(
    frame: pd.DataFrame,
    *,
    num_folds: int = NUM_FOLDS,
    fold: int = FOLD,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 <= fold < num_folds:
        raise ValueError(f"fold must be in [0, {num_folds}); got {fold}.")
    splitter = KFold(n_splits=num_folds, shuffle=True, random_state=seed)
    train_index, test_index = list(splitter.split(frame))[fold]
    return (
        frame.iloc[train_index].reset_index(drop=True),
        frame.iloc[test_index].reset_index(drop=True),
    )


def stage_cohort(
    source_dir: Path,
    workspace_dir: Path,
    private_dir: Path,
    *,
    num_folds: int = NUM_FOLDS,
    fold: int = FOLD,
    seed: int = SEED,
) -> dict[str, object]:
    frame, features, preprocessing = load_cohort(source_dir)
    train, test = split_cohort(frame, num_folds=num_folds, fold=fold, seed=seed)
    if test["sample_id"].duplicated().any():
        raise ValueError("selected test fold contains duplicate PATIENT_ID values")

    workspace_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    visible_columns = ["sample_id", *features]

    train[visible_columns + _OUTCOME_COLUMNS[1:]].to_csv(
        workspace_dir / "train.csv", index=False
    )
    test[visible_columns].to_csv(workspace_dir / "test_examples.csv", index=False)

    # The verifier uses private copies because the agent may modify /workspace.
    train[_OUTCOME_COLUMNS].to_csv(private_dir / "train_outcomes.csv", index=False)
    test[_OUTCOME_COLUMNS].to_csv(private_dir / "test_labels.csv", index=False)

    manifest: dict[str, object] = {
        "dataset": DATASET_NAME,
        "cohort": COHORT,
        "prediction_task": PREDICTION_TASK,
        "num_folds": num_folds,
        "fold": fold,
        "seed": seed,
        "n_train": len(train),
        "n_test": len(test),
        "features": features,
        **preprocessing,
    }
    (workspace_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--workspace-dir", type=Path, default=Path("/workspace/data"))
    parser.add_argument("--private-dir", type=Path, default=Path("/tests"))
    args = parser.parse_args()

    manifest = stage_cohort(
        args.source_dir,
        args.workspace_dir,
        args.private_dir,
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
