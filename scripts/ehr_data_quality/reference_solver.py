"""Heuristic reference solver for the ehr_data_quality benchmark.

Reads corrupted CSVs from ``--data-dir/csv/`` and writes a list of suspected
problematic rows to ``--output``. Implements straightforward per-family
detectors without any knowledge of the per-task seed or which family is active,
so it can run on any of the four tasks and yield a non-trivial F1.

Detection coverage:

- **impossible_value**:
  - hard physiological range checks (catches range_extreme; usually ×100
    decimal_shift; usually unit_confusion when factor is large)
  - per-itemid Z-score outliers (catches the in-range decimal_shift case
    and the smaller unit-confusion factors)
  - per-itemid majority-vote on ``valueuom`` (catches valueuom_mismatch)
  - per-drug Z-score outliers on ``dose_val_rx`` (catches decimal_shift_rx)

- **temporal_violation**:
  - ``dischtime < admittime`` per admission row
  - prescription ``starttime > admissions.dischtime`` for the matching hadm

- **inconsistency**:
  - in_table: groupby ``(subject_id, charttime, itemid)`` with multiple
    distinct ``valuenum``
  - cross_table: lab/chart paired itemids at the same patient/charttime
    differing by > 30%

- **demographic_conflict**:
  - patients whose recorded gender is opposite to a strongly gender-marker
    drug they were prescribed
  - patients < 30 years old who were prescribed a geriatric-only drug

Usage:
    python reference_solver.py --data-dir /workspace/data --output /workspace/submission/flagged_rows.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Plausibility ranges per (table, itemid). Slightly wider than RANGE_VIOLATIONS
# so the solver is independent of the injector internals.
PLAUSIBLE_RANGES: dict[str, dict[int, tuple[float, float]]] = {
    "labevents": {
        50912: (0.05, 25.0),  # creatinine
        50931: (20.0, 1000.0),  # glucose
        50971: (0.5, 10.0),  # potassium
        50983: (90.0, 220.0),  # sodium
        50885: (0.1, 30.0),  # bilirubin total
    },
    "chartevents": {
        220045: (15, 260),  # heart rate
        220179: (30, 260),  # SBP NI
        220180: (15, 210),  # DBP NI
        223761: (75.0, 115.0),  # temp F
        220277: (40, 105),  # SpO2
    },
}

# Kept in sync with ``inject.py``'s GENDER_DRUG_HINTS. The full marker drug
# list is retained for evidence-side detection (the agent should still link
# a Tamsulosin prescription with the patient's sex when reasoning about
# ref_range swaps, even though Tamsulosin itself is not used as a
# `gender_via_prescription_swap` corruption target — see
# inject.py:EXCLUDED_GENDER_MARKER_DRUGS).
GENDER_DRUGS: dict[str, list[str]] = {
    "F": [
        "Estradiol", "Estrogen", "Tamoxifen", "Anastrozole",
        "Levonorgestrel", "Norethindrone", "Medroxyprogesterone",
    ],
    "M": [
        "Sildenafil", "Tadalafil", "Vardenafil", "Finasteride",
        "Dutasteride", "Tamsulosin", "Testosterone",
    ],
}
GERIATRIC_DRUGS: list[str] = ["Donepezil", "Memantine", "Rivastigmine", "Galantamine"]
LAB_CHART_PAIRS: dict[int, int] = {
    50931: 225664,  # glucose
    50983: 220645,  # sodium
    50912: 220615,  # creatinine
    51222: 220228,  # hemoglobin
}

# Z-score threshold for per-itemid outliers. Lower → more flags (higher recall,
# lower precision); higher → fewer flags. 8.0 still catches ×10 decimal shifts
# (which produce ~10–30σ values) while suppressing the long natural tail of
# real-but-suspicious values that exist in the demo.
Z_THRESHOLD = 8.0
# Per-drug Z-score threshold for dose outliers. ×10/×100 dose mutations push
# the value many σ above the per-drug mean, so a stricter bar still catches
# them while skipping legitimate dose variability.
DOSE_Z_THRESHOLD = 10.0
# Cross-table relative-difference threshold. Injection uses ×1.5 (50% off);
# lab/chart variance for the same analyte at the same minute is typically
# under 25%, so 0.40 is a comfortable floor.
CROSS_TABLE_DIFF_THRESHOLD = 0.40


def _read(data_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(
        data_dir / "csv" / f"{name}.csv.gz", compression="gzip", low_memory=False
    )


def _flag(rows: list[dict], table: str, row_ids: pd.Series) -> None:
    if row_ids is None or len(row_ids) == 0:
        return
    for rid in pd.Series(row_ids).dropna().astype(str).unique():
        rows.append({"table": table, "_row_id": rid})


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def detect_range_violations(data_dir: Path, flagged: list[dict]) -> None:
    for table in ("labevents", "chartevents"):
        df = _read(data_dir, table)
        if "valuenum" not in df.columns or "itemid" not in df.columns:
            continue
        for itemid, (lo, hi) in PLAUSIBLE_RANGES.get(table, {}).items():
            mask = (
                (df["itemid"] == itemid)
                & df["valuenum"].notna()
                & ((df["valuenum"] < lo) | (df["valuenum"] > hi))
            )
            _flag(flagged, table, df.loc[mask, "_row_id"])


def detect_per_itemid_outliers(data_dir: Path, flagged: list[dict]) -> None:
    """Catches in-range decimal_shift, unit_confusion, distributional outliers."""
    for table in ("labevents", "chartevents"):
        df = _read(data_dir, table)
        if "valuenum" not in df.columns or "itemid" not in df.columns:
            continue
        df = df.dropna(subset=["valuenum"])
        stats = df.groupby("itemid")["valuenum"].agg(["mean", "std"])
        stats = stats[stats["std"] > 0]
        merged = df.join(stats, on="itemid", how="inner")
        z = (merged["valuenum"] - merged["mean"]).abs() / merged["std"]
        mask = z > Z_THRESHOLD
        _flag(flagged, table, merged.loc[mask, "_row_id"])


def detect_valueuom_mismatch(data_dir: Path, flagged: list[dict]) -> None:
    """Flag labevents rows whose valueuom is rare for that itemid AND the
    deviation is by more than a 95%/5% split (handles real cases where the
    same itemid legitimately has a couple of unit variants).
    """
    df = _read(data_dir, "labevents")
    if "valueuom" not in df.columns or "itemid" not in df.columns:
        return
    counts = (
        df.groupby(["itemid", "valueuom"]).size().rename("n").reset_index()
    )
    if counts.empty:
        return
    totals = counts.groupby("itemid")["n"].sum().rename("total")
    counts = counts.join(totals, on="itemid")
    counts["share"] = counts["n"] / counts["total"]
    # A valueuom is "wrong" if it represents <5% of that itemid's rows AND the
    # itemid has at least 20 rows (so we can be sure of the modal unit).
    rare = counts[(counts["share"] < 0.05) & (counts["total"] >= 20)]
    if rare.empty:
        return
    rare_pairs = set(zip(rare["itemid"], rare["valueuom"], strict=True))
    df = df.copy()
    pair_series = list(zip(df["itemid"], df["valueuom"]))
    df["_is_rare"] = [p in rare_pairs for p in pair_series]
    mask = df["_is_rare"]
    _flag(flagged, "labevents", df.loc[mask, "_row_id"])


def detect_dose_outliers(data_dir: Path, flagged: list[dict]) -> None:
    df = _read(data_dir, "prescriptions")
    if "dose_val_rx" not in df.columns or "drug" not in df.columns:
        return

    def _to_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    df = df.copy()
    df["_dose_f"] = df["dose_val_rx"].apply(_to_float)
    df = df[df["_dose_f"].notna()]
    if df.empty:
        return
    stats = df.groupby("drug")["_dose_f"].agg(["mean", "std"])
    stats = stats[stats["std"] > 0]
    merged = df.join(stats, on="drug", how="inner")
    z = (merged["_dose_f"] - merged["mean"]).abs() / merged["std"]
    mask = z > DOSE_Z_THRESHOLD
    _flag(flagged, "prescriptions", merged.loc[mask, "_row_id"])


def detect_temporal_admissions(data_dir: Path, flagged: list[dict]) -> None:
    df = _read(data_dir, "admissions")
    df = df.copy()
    df["admittime"] = pd.to_datetime(df["admittime"], errors="coerce")
    df["dischtime"] = pd.to_datetime(df["dischtime"], errors="coerce")
    mask = df["dischtime"].notna() & df["admittime"].notna() & (
        df["dischtime"] < df["admittime"]
    )
    _flag(flagged, "admissions", df.loc[mask, "_row_id"])


def detect_med_after_discharge(data_dir: Path, flagged: list[dict]) -> None:
    rx = _read(data_dir, "prescriptions")
    adm = _read(data_dir, "admissions")[["hadm_id", "dischtime"]].copy()
    rx = rx.copy()
    rx["starttime"] = pd.to_datetime(rx["starttime"], errors="coerce")
    adm["dischtime"] = pd.to_datetime(adm["dischtime"], errors="coerce")
    merged = rx.merge(adm, on="hadm_id", how="left")
    mask = merged["starttime"].notna() & merged["dischtime"].notna() & (
        merged["starttime"] > merged["dischtime"]
    )
    _flag(flagged, "prescriptions", merged.loc[mask, "_row_id"])


def detect_in_table_duplicates(data_dir: Path, flagged: list[dict]) -> None:
    for table in ("labevents", "chartevents"):
        df = _read(data_dir, table)
        if "valuenum" not in df.columns:
            continue
        keys = ["subject_id", "charttime", "itemid"]
        if not all(k in df.columns for k in keys):
            continue
        df = df.dropna(subset=["valuenum"])
        grouped = df.groupby(keys)["valuenum"].nunique()
        suspicious = grouped[grouped > 1].index
        if len(suspicious) == 0:
            continue
        idx = pd.MultiIndex.from_arrays([df[k] for k in keys])
        mask = idx.isin(suspicious)
        _flag(flagged, table, df.loc[mask, "_row_id"])


def detect_cross_table_conflicts(data_dir: Path, flagged: list[dict]) -> None:
    le = _read(data_dir, "labevents")
    ce = _read(data_dir, "chartevents")
    le = le.copy()
    ce = ce.copy()
    le["charttime"] = pd.to_datetime(le["charttime"], errors="coerce")
    ce["charttime"] = pd.to_datetime(ce["charttime"], errors="coerce")
    for lab_id, chart_id in LAB_CHART_PAIRS.items():
        lab_sub = le[(le["itemid"] == lab_id) & le["valuenum"].notna()][
            ["_row_id", "subject_id", "charttime", "valuenum"]
        ].rename(columns={"_row_id": "_row_id_lab", "valuenum": "valuenum_lab"})
        chart_sub = ce[(ce["itemid"] == chart_id) & ce["valuenum"].notna()][
            ["_row_id", "subject_id", "charttime", "valuenum"]
        ].rename(columns={"_row_id": "_row_id_chart", "valuenum": "valuenum_chart"})
        if lab_sub.empty or chart_sub.empty:
            continue
        merged = lab_sub.merge(chart_sub, on=["subject_id", "charttime"])
        if merged.empty:
            continue
        denom = merged["valuenum_lab"].abs().clip(lower=1e-9)
        rel_diff = (merged["valuenum_chart"] - merged["valuenum_lab"]).abs() / denom
        mask = rel_diff > CROSS_TABLE_DIFF_THRESHOLD
        _flag(flagged, "labevents", merged.loc[mask, "_row_id_lab"])
        _flag(flagged, "chartevents", merged.loc[mask, "_row_id_chart"])


def detect_demographic_conflict(data_dir: Path, flagged: list[dict]) -> None:
    pat = _read(data_dir, "patients")
    rx = _read(data_dir, "prescriptions")
    if "drug" not in rx.columns or "gender" not in pat.columns:
        return

    # Gender mismatch: patients whose current gender is opposite to a marker drug
    for expected_gender, drug_list in GENDER_DRUGS.items():
        opposite = "M" if expected_gender == "F" else "F"
        for drug in drug_list:
            matches = rx[
                rx["drug"].astype(str).str.contains(drug, case=False, na=False)
            ]
            if matches.empty:
                continue
            sids = matches["subject_id"].unique()
            mask = pat["subject_id"].isin(sids) & (pat["gender"] == opposite)
            _flag(flagged, "patients", pat.loc[mask, "_row_id"])

    # Age mismatch: patients < 30 on geriatric-only drugs
    if "anchor_age" in pat.columns:
        for drug in GERIATRIC_DRUGS:
            matches = rx[
                rx["drug"].astype(str).str.contains(drug, case=False, na=False)
            ]
            if matches.empty:
                continue
            sids = matches["subject_id"].unique()
            try:
                ages = pat["anchor_age"].astype(float)
            except (TypeError, ValueError):
                continue
            mask = pat["subject_id"].isin(sids) & (ages < 30)
            _flag(flagged, "patients", pat.loc[mask, "_row_id"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    flagged: list[dict] = []
    detect_range_violations(args.data_dir, flagged)
    detect_per_itemid_outliers(args.data_dir, flagged)
    detect_valueuom_mismatch(args.data_dir, flagged)
    detect_dose_outliers(args.data_dir, flagged)
    detect_temporal_admissions(args.data_dir, flagged)
    detect_med_after_discharge(args.data_dir, flagged)
    detect_in_table_duplicates(args.data_dir, flagged)
    detect_cross_table_conflicts(args.data_dir, flagged)
    detect_demographic_conflict(args.data_dir, flagged)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(flagged)
    if df.empty:
        df = pd.DataFrame(columns=["table", "_row_id"])
    df = df.drop_duplicates(["table", "_row_id"])
    df.to_csv(args.output, index=False)
    print(f"reference_solver: wrote {len(df)} flagged rows to {args.output}")


if __name__ == "__main__":
    main()
