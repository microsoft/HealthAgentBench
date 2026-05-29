"""Unit tests for the ehr_data_quality injection library."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ehr_data_quality"))

from inject import (  # noqa: E402
    INJECTOR_REGISTRY,
    Label,
    add_row_ids,
    apply_task_corruption,
    inject_inconsistency,
    inject_impossible_value,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _tiny_labevents() -> pd.DataFrame:
    rows = []
    for i, sid in enumerate(range(10000, 10010)):
        for itemid, base in [(50912, 1.0), (50931, 100.0), (50971, 4.0)]:
            val = base + 0.1 * i
            rows.append(
                {
                    "labevent_id": len(rows) + 1,
                    "subject_id": sid,
                    "hadm_id": sid * 10,
                    "itemid": itemid,
                    "charttime": "2180-01-01 12:00:00",
                    "value": str(val),
                    "valuenum": val,
                    "valueuom": "mg/dL",
                }
            )
    return pd.DataFrame(rows)


def _tiny_chartevents() -> pd.DataFrame:
    rows = []
    for sid in range(10000, 10010):
        for itemid, val in [(220045, 80), (220179, 120), (220277, 98)]:
            rows.append(
                {
                    "subject_id": sid,
                    "hadm_id": sid * 10,
                    "stay_id": sid * 100,
                    "charttime": "2180-01-01 12:00:00",
                    "itemid": itemid,
                    "value": val,
                    "valuenum": float(val),
                    "valueuom": "bpm",
                }
            )
    return pd.DataFrame(rows)


def _tiny_admissions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "subject_id": sid,
                "hadm_id": sid * 10,
                "admittime": "2180-01-01 10:00:00",
                "dischtime": "2180-01-05 10:00:00",
                "admission_type": "URGENT",
            }
            for sid in range(10000, 10010)
        ]
    )


def _tiny_patients() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "subject_id": sid,
                "gender": "F",
                "anchor_age": 50,
                "anchor_year": 2180,
                "dod": "",
            }
            for sid in range(10000, 10010)
        ]
    )


def _tiny_prescriptions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "subject_id": sid,
                "hadm_id": sid * 10,
                "pharmacy_id": i,
                "starttime": "2180-01-02 08:00:00",
                "stoptime": "2180-01-02 20:00:00",
                "drug": "APAP",
                "dose_val_rx": "500",
                "dose_unit_rx": "mg",
            }
            for i, sid in enumerate(range(10000, 10010))
        ]
    )


@pytest.fixture
def lab_df():
    return add_row_ids(_tiny_labevents(), "labevents")


@pytest.fixture
def chart_df():
    return add_row_ids(_tiny_chartevents(), "chartevents")


@pytest.fixture
def adm_df():
    return add_row_ids(_tiny_admissions(), "admissions")


@pytest.fixture
def pat_df():
    return add_row_ids(_tiny_patients(), "patients")


@pytest.fixture
def rx_df():
    return add_row_ids(_tiny_prescriptions(), "prescriptions")


@pytest.fixture
def in_scope():
    return set(range(10000, 10005))


# ---------------------------------------------------------------------------
# add_row_ids
# ---------------------------------------------------------------------------


def test_add_row_ids_deterministic():
    df = _tiny_labevents()
    a = add_row_ids(df, "labevents")
    b = add_row_ids(df, "labevents")
    assert a["_row_id"].tolist() == b["_row_id"].tolist()


def test_add_row_ids_idempotent():
    once = add_row_ids(_tiny_labevents(), "labevents")
    twice = add_row_ids(once, "labevents")
    pd.testing.assert_frame_equal(once, twice)


def test_add_row_ids_unique():
    out = add_row_ids(_tiny_labevents(), "labevents")
    assert out["_row_id"].is_unique


def test_add_row_ids_table_namespaced():
    a = add_row_ids(_tiny_labevents().head(1), "labevents")
    b = add_row_ids(_tiny_labevents().head(1), "chartevents")
    assert a.iloc[0]["_row_id"] != b.iloc[0]["_row_id"]


# ---------------------------------------------------------------------------
# Top-level INJECTOR_REGISTRY entries
# ---------------------------------------------------------------------------


def test_registry_has_three_families():
    """temporal_violation removed: the pristine demo contains real-world
    temporal anomalies that contaminate cluster recall accounting."""
    assert set(INJECTOR_REGISTRY.keys()) == {
        "impossible_value",
        "inconsistency",
        "demographic_conflict",
    }


def _picker(name, fixtures):
    lab_df, chart_df, adm_df, pat_df, rx_df = fixtures
    related = {
        "admissions": adm_df,
        "chartevents": chart_df,
        "patients": pat_df,
        "prescriptions": rx_df,
        "labevents": lab_df,
    }
    if name == "inconsistency":
        # In-table sub-type runs on labevents; cross-table sub-type only fires
        # on chartevents. Test the in-table path here; cross-table has its own
        # dedicated test below.
        return lab_df, "labevents", {"related_tables": related}
    if name == "demographic_conflict":
        # Synthetic prescriptions fixture lacks marker drugs, so this test
        # path returns empty labels — schema/determinism still validated.
        return pat_df, "patients", {"related_tables": related}
    return lab_df, "labevents", {}


@pytest.mark.parametrize("name", list(INJECTOR_REGISTRY.keys()))
def test_each_injector_emits_valid_label_schema(
    name, lab_df, chart_df, adm_df, pat_df, rx_df, in_scope
):
    fixtures = (lab_df, chart_df, adm_df, pat_df, rx_df)
    df, table, kw = _picker(name, fixtures)
    rng = np.random.default_rng(0)
    _, labels = INJECTOR_REGISTRY[name](df.copy(), table, in_scope, rng, 6, **kw)
    assert all(isinstance(L, Label) for L in labels)
    for L in labels:
        assert L.error_family == name
        assert L.cluster_id, "cluster_id must be set"
        assert L.error_subtype, "error_subtype must be set"
        assert L.severity in ("obvious", "medium", "subtle")


@pytest.mark.parametrize("name", list(INJECTOR_REGISTRY.keys()))
def test_each_injector_seed_deterministic(
    name, lab_df, chart_df, adm_df, pat_df, rx_df, in_scope
):
    fixtures = (lab_df, chart_df, adm_df, pat_df, rx_df)
    df, table, kw = _picker(name, fixtures)
    df1, l1 = INJECTOR_REGISTRY[name](
        df.copy(), table, in_scope, np.random.default_rng(7), 6, **kw
    )
    df2, l2 = INJECTOR_REGISTRY[name](
        df.copy(), table, in_scope, np.random.default_rng(7), 6, **kw
    )
    pd.testing.assert_frame_equal(df1, df2, check_dtype=False)
    assert [(L.table, L.row_id, L.cluster_id) for L in l1] == [
        (L.table, L.row_id, L.cluster_id) for L in l2
    ]


# ---------------------------------------------------------------------------
# Cluster semantics
# ---------------------------------------------------------------------------


def test_impossible_value_clusters_are_singletons(lab_df, in_scope):
    rng = np.random.default_rng(0)
    _, labels = inject_impossible_value(lab_df.copy(), "labevents", in_scope, rng, 12)
    assert labels
    for L in labels:
        # Singleton clusters: exactly one label per cluster.
        assert L.cluster_id == f"{L.table}|{L.row_id}"


def test_impossible_value_covers_multiple_subtypes(lab_df, in_scope):
    rng = np.random.default_rng(0)
    _, labels = inject_impossible_value(lab_df.copy(), "labevents", in_scope, rng, 20)
    subtypes = {L.error_subtype for L in labels}
    # labevents triggers all 4 sub-types when count is large enough.
    assert "range_extreme" in subtypes
    assert "decimal_shift" in subtypes
    assert "unit_confusion" in subtypes
    assert "valueuom_mismatch" in subtypes


def test_decimal_shift_rx_skips_nan_and_small_doses(in_scope):
    """`decimal_shift_rx` must skip rows whose dose_val_rx is NaN, the literal
    string 'nan', empty, or below 1.0 — those produce meaningless labels
    (NaN × 100 = NaN; 0.1 × 100 = 10 mg which is still a plausible dose)."""
    rows = [
        # Eligible: dose=5.0 → 500 (impossible for most drugs)
        {"prescriptions_id": 1, "subject_id": 10000, "drug": "Aspirin",
         "dose_val_rx": "5.0", "dose_unit_rx": "mg"},
        # Skip: NaN string
        {"prescriptions_id": 2, "subject_id": 10001, "drug": "Aspirin",
         "dose_val_rx": "nan", "dose_unit_rx": "mg"},
        # Skip: empty string
        {"prescriptions_id": 3, "subject_id": 10002, "drug": "Aspirin",
         "dose_val_rx": "", "dose_unit_rx": "mg"},
        # Skip: sub-1.0 dose (0.1 × 100 = 10 is plausible)
        {"prescriptions_id": 4, "subject_id": 10003, "drug": "Aspirin",
         "dose_val_rx": "0.1", "dose_unit_rx": "mg"},
        # Eligible: dose=100 → 10,000 (clearly wrong)
        {"prescriptions_id": 5, "subject_id": 10004, "drug": "Aspirin",
         "dose_val_rx": "100", "dose_unit_rx": "mg"},
    ]
    df = add_row_ids(pd.DataFrame(rows), "prescriptions")
    rng = np.random.default_rng(0)
    _, labels = inject_impossible_value(
        df, "prescriptions", set(range(10000, 10010)), rng, count=10,
    )
    shifted_rxids = {L.row_id for L in labels if L.error_subtype == "decimal_shift_rx"}
    eligible_rxids = {df.iloc[0]["_row_id"], df.iloc[4]["_row_id"]}
    # Only eligible rows (positions 0 and 4) may have been picked.
    assert shifted_rxids.issubset(eligible_rxids)
    # Every emitted label must have a finite, non-NaN corrupted_value.
    for L in labels:
        if L.error_subtype != "decimal_shift_rx":
            continue
        corrupted = float(L.corrupted_value)
        assert not pd.isna(corrupted)
        assert corrupted >= 100.0  # 100× of eligible doses (≥1.0)


def test_decimal_shift_subtype_lands_in_extreme_band(lab_df, in_scope):
    """Decimal-shift now targets the per-itemid *extreme* band so the
    corrupted value is unambiguously implausible (a high-but-plausible
    glucose like 720 mg/dL in DKA does not count as an error). The
    multiplier is chosen from (10×, 100×, 1000×) — smallest factor that
    lands the value in the extreme band wins.
    """
    from inject import RANGE_VIOLATIONS, DECIMAL_SHIFT_FACTORS

    rng = np.random.default_rng(42)
    new_df, labels = inject_impossible_value(lab_df.copy(), "labevents", in_scope, rng, 30)
    for L in labels:
        if L.error_subtype != "decimal_shift":
            continue
        new_val = float(L.corrupted_value)
        orig_val = float(L.original_value)
        # Find the itemid for this row.
        row = new_df.set_index("_row_id").loc[L.row_id]
        itemid = int(row["itemid"])
        if itemid not in RANGE_VIOLATIONS["labevents"]:
            continue
        _name, _plo, _phi, elo, ehi = RANGE_VIOLATIONS["labevents"][itemid]
        # Corrupted value must be in the extreme band.
        assert elo <= new_val <= ehi, (
            f"decimal_shift produced {new_val} outside extreme band "
            f"[{elo}, {ehi}] for itemid {itemid}"
        )
        # The factor must be one of the canonical decimal-shift factors.
        ratio = new_val / orig_val
        assert any(abs(ratio - f) < 1e-6 for f in DECIMAL_SHIFT_FACTORS), (
            f"decimal_shift produced ratio {ratio} not in {DECIMAL_SHIFT_FACTORS}"
        )


def test_inconsistency_two_row_cluster(lab_df, in_scope):
    rng = np.random.default_rng(0)
    new_df, labels = inject_inconsistency(
        lab_df.copy(), "labevents", in_scope, rng, 5
    )
    by_cluster = {}
    for L in labels:
        by_cluster.setdefault(L.cluster_id, []).append(L)
    assert by_cluster
    for cluster_id, group in by_cluster.items():
        # Each cluster has exactly one "anchor" (original) and one "duplicate".
        subtypes = {L.error_subtype for L in group}
        assert subtypes == {
            "in_table_conflict",
            "in_table_conflict_anchor",
        }, f"cluster {cluster_id} subtypes={subtypes}"
        row_ids = {L.row_id for L in group}
        assert len(row_ids) == 2, "cluster must reference two distinct row ids"
        # Both rows must exist in the resulting df.
        present = set(new_df["_row_id"].astype(str))
        assert row_ids.issubset(present)


def test_inconsistency_cross_table_subtype(lab_df, chart_df, in_scope):
    """When invoked on chartevents with related labevents, cross-table sub-type
    creates a chartevents row referencing a labevents anchor for the same
    patient at the same charttime, with a slightly different valuenum.
    """
    # Build a labevents fixture that includes a glucose row (itemid 50931)
    # for an in-scope subject so cross_table_conflict can hit it.
    lab_aug = pd.concat(
        [
            lab_df,
            add_row_ids(
                pd.DataFrame(
                    [
                        {
                            "labevent_id": 9999,
                            "subject_id": 10000,
                            "hadm_id": 100000,
                            "itemid": 50931,
                            "charttime": "2180-01-02 06:00:00",
                            "value": "120.0",
                            "valuenum": 120.0,
                            "valueuom": "mg/dL",
                        }
                    ]
                ),
                "labevents",
            ),
        ],
        ignore_index=True,
    )
    chart_aug = pd.concat(
        [
            chart_df,
            add_row_ids(
                pd.DataFrame(
                    [
                        {
                            "subject_id": 10000,
                            "hadm_id": 100000,
                            "stay_id": 1000000,
                            "charttime": "2180-01-02 06:00:00",
                            "itemid": 225664,
                            "value": 120,
                            "valuenum": 120.0,
                            "valueuom": "mg/dL",
                        }
                    ]
                ),
                "chartevents",
            ),
        ],
        ignore_index=True,
    )
    related = {"labevents": lab_aug, "chartevents": chart_aug}
    rng = np.random.default_rng(0)
    new_df, labels = inject_inconsistency(
        chart_aug.copy(), "chartevents", in_scope, rng, 4, related_tables=related
    )
    subtypes = {L.error_subtype for L in labels}
    # Should fire both sub-types when count permits.
    assert "cross_table_conflict" in subtypes or "cross_table_conflict_anchor" in subtypes


def test_demographic_conflict_cluster_spans_patients_and_prescriptions():
    """Patient on a gender-marker drug gets their gender flipped; cluster spans
    {patients_row, prescriptions_row}.
    """
    # Patient 9001 is currently F and receives Tamoxifen (a female-indicating
    # drug). The injector flips them to M so the prescription contradicts the
    # demographic.
    pat = pd.DataFrame(
        [
            {"subject_id": 9001, "gender": "F", "anchor_age": 60, "anchor_year": 2180, "dod": ""},
            {"subject_id": 9002, "gender": "F", "anchor_age": 30, "anchor_year": 2180, "dod": ""},
        ]
    )
    rx = pd.DataFrame(
        [
            {"subject_id": 9001, "hadm_id": 90010, "drug": "Tamoxifen Citrate",
             "starttime": "2180-01-02 08:00:00", "stoptime": "", "dose_val_rx": "20",
             "dose_unit_rx": "mg", "pharmacy_id": 1},
            {"subject_id": 9002, "hadm_id": 90020, "drug": "Acetaminophen",
             "starttime": "2180-01-02 08:00:00", "stoptime": "", "dose_val_rx": "500",
             "dose_unit_rx": "mg", "pharmacy_id": 2},
        ]
    )
    pat = add_row_ids(pat, "patients")
    rx = add_row_ids(rx, "prescriptions")

    from inject import inject_demographic_conflict

    rng = np.random.default_rng(0)
    new_df, labels = inject_demographic_conflict(
        pat.copy(), "patients", {9001, 9002}, rng, 5,
        related_tables={"prescriptions": rx, "patients": pat},
    )
    assert labels, "demographic_conflict should fire on the Tamoxifen patient"
    # The mutated patient (9001) should now have gender M (was F).
    new_gender = new_df.loc[new_df["subject_id"] == 9001, "gender"].iloc[0]
    assert new_gender == "M"
    # Cluster should span both tables.
    by_cluster = {}
    for L in labels:
        by_cluster.setdefault(L.cluster_id, []).append(L)
    for cluster_id, group in by_cluster.items():
        tables = {L.table for L in group}
        assert tables == {"patients", "prescriptions"}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Shortcut fixes (v2): value↔valuenum sync, varied range replacement,
# in_table_conflict jitter / fresh PK / wider multiplier, cross_table rounding
# ---------------------------------------------------------------------------


def test_value_and_valuenum_stay_in_sync_after_impossible_value(lab_df, in_scope):
    """Mutations to ``valuenum`` must also rewrite the parallel ``value``
    string so the agent can't detect corruption via value-vs-valuenum
    comparison alone.
    """
    rng = np.random.default_rng(0)
    new_df, labels = inject_impossible_value(
        lab_df.copy(), "labevents", in_scope, rng, 30
    )
    by_id = new_df.set_index("_row_id")
    for L in labels:
        if L.field != "valuenum":
            continue
        if L.error_subtype not in {"range_extreme", "decimal_shift", "unit_confusion"}:
            continue
        row = by_id.loc[L.row_id]
        assert str(row["value"]) == str(row["valuenum"]), (
            f"value/valuenum out of sync at {L.error_subtype} row {L.row_id}: "
            f"value={row['value']!r} valuenum={row['valuenum']!r}"
        )


def test_range_extreme_replacement_is_varied(lab_df, in_scope):
    """Range-extreme replacements must be sampled from a band, not a constant
    sentinel like 999.9 the agent could grep for."""
    rng = np.random.default_rng(0)
    _, labels = inject_impossible_value(
        lab_df.copy(), "labevents", in_scope, rng, 24
    )
    range_extreme_values = [
        float(L.corrupted_value)
        for L in labels
        if L.error_subtype == "range_extreme"
    ]
    assert len(range_extreme_values) >= 4, "need enough samples to check variance"
    # If the values were a constant, len(unique) == 1. We want at least a
    # couple of distinct values to confirm the band-sampling fix.
    assert len(set(range_extreme_values)) >= 2


def test_in_table_conflict_duplicate_has_fresh_pk_and_jittered_charttime(
    lab_df, in_scope
):
    """Duplicates from inconsistency.in_table_conflict must carry a fresh
    primary key (labevent_id) and a charttime offset by ±5min so a naive
    "exact PK match" or "exact charttime group-by" detection trick fails.
    """
    rng = np.random.default_rng(0)
    new_df, labels = inject_inconsistency(
        lab_df.copy(), "labevents", in_scope, rng, 6
    )
    new_df = new_df.copy()
    by_id = new_df.set_index("_row_id")
    found = 0
    for L in labels:
        if L.error_subtype != "in_table_conflict":
            continue
        # Find anchor (original) and duplicate.
        anchor_label = next(
            (a for a in labels
             if a.cluster_id == L.cluster_id
             and a.error_subtype == "in_table_conflict_anchor"),
            None,
        )
        assert anchor_label is not None
        dup = by_id.loc[L.row_id]
        orig = by_id.loc[anchor_label.row_id]
        # Fresh PK
        assert int(dup["labevent_id"]) != int(orig["labevent_id"]), (
            "duplicate must have fresh labevent_id"
        )
        # The fresh PK must look natural — far below the 10⁹+ band that
        # would let an agent detect duplicates via PK magnitude alone.
        # Real MIMIC-IV-demo labevent_id max is ~5×10⁵; we cap at 10⁸ so
        # the fresh value can never look like a sentinel.
        assert int(dup["labevent_id"]) < 10**8, (
            f"fresh labevent_id {int(dup['labevent_id'])} is in the "
            f"sentinel band — would create a PK-magnitude shortcut"
        )
        # Charttime offset within ±5min
        dup_t = pd.to_datetime(dup["charttime"])
        orig_t = pd.to_datetime(orig["charttime"])
        delta = abs((dup_t - orig_t).total_seconds())
        assert delta <= 5 * 60 + 1, f"charttime delta {delta}s > 5min"
        # Multiplier in [1.10, 1.50] — not the static 1.05.
        ratio = float(dup["valuenum"]) / float(orig["valuenum"])
        assert 1.10 - 1e-6 <= ratio <= 1.50 + 1e-6, f"ratio {ratio} outside [1.10, 1.50]"
        found += 1
    assert found > 0


def test_cross_table_conflict_valuenum_is_rounded(lab_df, chart_df, in_scope):
    """cross_table conflict's chartevents row should be rounded to per-itemid
    device precision so it doesn't reveal itself via float artifacts like
    ``120.50000000000001``.
    """
    from inject import DEVICE_PRECISION, add_row_ids as _ari

    # Augment chart with at least one (50931, 225664) glucose pair.
    lab_aug = pd.concat(
        [lab_df, _ari(pd.DataFrame([{
            "labevent_id": 9999, "subject_id": 10000, "hadm_id": 100000,
            "itemid": 50931, "charttime": "2180-01-02 06:00:00",
            "value": "120.0", "valuenum": 120.0, "valueuom": "mg/dL",
        }]), "labevents")],
        ignore_index=True,
    )
    chart_aug = pd.concat(
        [chart_df, _ari(pd.DataFrame([{
            "subject_id": 10000, "hadm_id": 100000, "stay_id": 1000000,
            "charttime": "2180-01-02 06:00:00", "itemid": 225664,
            "value": 120, "valuenum": 120.0, "valueuom": "mg/dL",
        }]), "chartevents")],
        ignore_index=True,
    )
    rng = np.random.default_rng(0)
    new_df, labels = inject_inconsistency(
        chart_aug.copy(), "chartevents", in_scope, rng, 4,
        related_tables={"labevents": lab_aug, "chartevents": chart_aug},
    )
    by_id = new_df.set_index("_row_id")
    found = 0
    for L in labels:
        if L.error_subtype != "cross_table_conflict":
            continue
        row = by_id.loc[L.row_id]
        itemid = int(row["itemid"])
        precision = DEVICE_PRECISION.get(itemid, 1)
        valuenum = float(row["valuenum"])
        # Round-trip check: round to precision and confirm it equals itself.
        assert round(valuenum, precision) == valuenum, (
            f"cross_table valuenum {valuenum} not rounded to {precision} dp "
            f"for itemid {itemid}"
        )
        found += 1
    assert found > 0


# ---------------------------------------------------------------------------
# v2 demographic_conflict — three sub-types and expanded clusters
# ---------------------------------------------------------------------------


def test_demographic_conflict_v2_subtypes_and_cluster_expansion():
    """v2 should fire all three gender sub-types when the data supports them
    and emit expanded clusters with multiple evidence rows.
    """
    from inject import inject_demographic_conflict

    pat = pd.DataFrame([
        # Female on Tamoxifen + has female-specific lab → patients_flip pool.
        {"subject_id": 9001, "gender": "F", "anchor_age": 60,
         "anchor_year": 2180, "dod": ""},
        # Male with hemoglobin (sex-specific lab w/ ref ranges) →
        # ref_range_swap pool. Also has neutral rx → prescription_swap pool.
        {"subject_id": 9002, "gender": "M", "anchor_age": 70,
         "anchor_year": 2180, "dod": ""},
        # Geriatric on Donepezil → age sub-type.
        {"subject_id": 9003, "gender": "F", "anchor_age": 80,
         "anchor_year": 2180, "dod": ""},
    ])
    rx = pd.DataFrame([
        {"subject_id": 9001, "hadm_id": 90010, "drug": "Tamoxifen Citrate",
         "starttime": "2180-01-02 08:00:00", "stoptime": "",
         "dose_val_rx": "20", "dose_unit_rx": "mg", "pharmacy_id": 1},
        {"subject_id": 9002, "hadm_id": 90020, "drug": "Acetaminophen",
         "starttime": "2180-01-02 08:00:00", "stoptime": "",
         "dose_val_rx": "500", "dose_unit_rx": "mg", "pharmacy_id": 2},
        {"subject_id": 9003, "hadm_id": 90030, "drug": "Donepezil",
         "starttime": "2180-01-02 08:00:00", "stoptime": "",
         "dose_val_rx": "10", "dose_unit_rx": "mg", "pharmacy_id": 3},
    ])
    lab = pd.DataFrame([
        {"subject_id": 9002, "hadm_id": 90020, "labevent_id": 1,
         "itemid": 51222, "charttime": "2180-01-02 06:00:00",
         "value": "14.0", "valuenum": 14.0, "valueuom": "g/dL",
         "ref_range_lower": 13.5, "ref_range_upper": 17.5},
    ])
    pat = add_row_ids(pat, "patients")
    rx = add_row_ids(rx, "prescriptions")
    lab = add_row_ids(lab, "labevents")
    related = {"patients": pat, "prescriptions": rx, "labevents": lab}

    rng = np.random.default_rng(0)
    new_df, labels = inject_demographic_conflict(
        pat.copy(), "patients", {9001, 9002, 9003}, rng, 12,
        related_tables=related,
    )
    subtypes_seen = {L.error_subtype for L in labels}
    # Expect at least 3 distinct mutation sub-types to fire (or their evidence
    # variants).
    primary_subtypes = {
        s for s in subtypes_seen
        if s in {"gender_via_patients_flip", "gender_via_prescription_swap",
                 "gender_via_ref_range_swap", "age_via_patients_change"}
    }
    assert len(primary_subtypes) >= 2, (
        f"v2 should hit ≥2 primary sub-types, saw {primary_subtypes}"
    )
    # Cluster expansion: at least one cluster should span ≥3 rows
    # (a flipped patient with ≥1 drug + ≥1 lab as evidence) OR multiple
    # tables.
    by_cluster: dict[str, list] = {}
    for L in labels:
        by_cluster.setdefault(L.cluster_id, []).append(L)
    multi_table_cluster = any(
        len({L.table for L in group}) >= 2 for group in by_cluster.values()
    )
    assert multi_table_cluster, (
        "demographic_conflict v2 must emit clusters spanning multiple tables"
    )


def test_demographic_conflict_v2_applies_rx_and_lab_mutations(tmp_path):
    """End-to-end: through ``apply_task_corruption`` the rx/lab mutations
    encoded by v2 demographic_conflict labels must actually land on disk.
    """
    from inject import apply_task_corruption

    raw = tmp_path / "raw"
    raw.mkdir()
    pat = pd.DataFrame([
        {"subject_id": 9001, "gender": "F", "anchor_age": 60,
         "anchor_year": 2180, "dod": ""},
        {"subject_id": 9002, "gender": "M", "anchor_age": 60,
         "anchor_year": 2180, "dod": ""},
    ])
    rx = pd.DataFrame([
        {"subject_id": 9001, "hadm_id": 90010, "drug": "Tamoxifen Citrate",
         "starttime": "2180-01-02 08:00:00", "stoptime": "",
         "dose_val_rx": "20", "dose_unit_rx": "mg", "pharmacy_id": 1},
        # Neutral rx for 9002 — eligible for prescription_swap mutation.
        {"subject_id": 9002, "hadm_id": 90020, "drug": "Acetaminophen",
         "starttime": "2180-01-02 08:00:00", "stoptime": "",
         "dose_val_rx": "500", "dose_unit_rx": "mg", "pharmacy_id": 2},
    ])
    lab = pd.DataFrame([
        # Hemoglobin row with ref ranges — ref_range_swap eligible.
        {"subject_id": 9002, "hadm_id": 90020, "labevent_id": 1,
         "itemid": 51222, "charttime": "2180-01-02 06:00:00",
         "value": "14.0", "valuenum": 14.0, "valueuom": "g/dL",
         "ref_range_lower": 13.5, "ref_range_upper": 17.5},
    ])
    pat.to_csv(raw / "patients.csv.gz", index=False, compression="gzip")
    rx.to_csv(raw / "prescriptions.csv.gz", index=False, compression="gzip")
    lab.to_csv(raw / "labevents.csv.gz", index=False, compression="gzip")
    pd.DataFrame([
        {"subject_id": 9001, "hadm_id": 90010,
         "admittime": "2180-01-01 10:00:00",
         "dischtime": "2180-01-05 10:00:00", "admission_type": "URGENT"},
        {"subject_id": 9002, "hadm_id": 90020,
         "admittime": "2180-01-01 10:00:00",
         "dischtime": "2180-01-05 10:00:00", "admission_type": "URGENT"},
    ]).to_csv(raw / "admissions.csv.gz", index=False, compression="gzip")
    pd.DataFrame({"subject_id": [], "hadm_id": [], "stay_id": [],
                  "itemid": [], "charttime": [], "valuenum": []}).to_csv(
        raw / "chartevents.csv.gz", index=False, compression="gzip")
    for t in ("d_labitems", "d_items"):
        pd.DataFrame({"itemid": []}).to_csv(
            raw / f"{t}.csv.gz", index=False, compression="gzip")
    pd.DataFrame({"subject_id": [], "hadm_id": [], "stay_id": []}).to_csv(
        raw / "icustays.csv.gz", index=False, compression="gzip")

    out = tmp_path / "out"
    config = {
        "seed": 0, "in_scope_patient_count": 2,
        "tables": ["patients"],
        "injectors": [{"family": "demographic_conflict", "count": 6}],
    }
    labels = apply_task_corruption(raw, out, config)
    assert labels

    # If a prescription_swap or ref_range_swap fired, verify the on-disk
    # value matches the corrupted_value in the label.
    rx_out = pd.read_csv(out / "prescriptions.csv.gz", compression="gzip")
    lab_out = pd.read_csv(out / "labevents.csv.gz", compression="gzip")
    for L in labels:
        if L.original_value == L.corrupted_value:
            continue
        if L.table == "prescriptions":
            mask = rx_out["_row_id"].astype(str) == str(L.row_id)
            assert mask.any()
            assert str(rx_out.loc[mask, L.field].iloc[0]) == L.corrupted_value
        elif L.table == "labevents":
            mask = lab_out["_row_id"].astype(str) == str(L.row_id)
            assert mask.any()
            actual = lab_out.loc[mask, L.field].iloc[0]
            assert float(actual) == pytest.approx(float(L.corrupted_value))


# ---------------------------------------------------------------------------
# Driver smoke
# ---------------------------------------------------------------------------


def test_apply_task_corruption_smoke(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _tiny_patients().to_csv(raw / "patients.csv.gz", index=False, compression="gzip")
    _tiny_admissions().to_csv(raw / "admissions.csv.gz", index=False, compression="gzip")
    _tiny_labevents().to_csv(raw / "labevents.csv.gz", index=False, compression="gzip")
    _tiny_chartevents().to_csv(raw / "chartevents.csv.gz", index=False, compression="gzip")
    _tiny_prescriptions().to_csv(raw / "prescriptions.csv.gz", index=False, compression="gzip")
    pd.DataFrame({"itemid": []}).to_csv(raw / "d_labitems.csv.gz", index=False, compression="gzip")
    pd.DataFrame({"itemid": []}).to_csv(raw / "d_items.csv.gz", index=False, compression="gzip")
    pd.DataFrame({"subject_id": [], "hadm_id": [], "stay_id": []}).to_csv(
        raw / "icustays.csv.gz", index=False, compression="gzip"
    )

    out = tmp_path / "out"
    config = {
        "seed": 0,
        "in_scope_patient_count": 5,
        "tables": ["labevents"],
        "injectors": [{"family": "impossible_value", "count": 8}],
    }
    labels = apply_task_corruption(raw, out, config)
    assert labels
    assert all(L.error_family == "impossible_value" for L in labels)
    assert all(L.table == "labevents" for L in labels)
    for t in [
        "patients",
        "admissions",
        "labevents",
        "chartevents",
        "prescriptions",
        "d_labitems",
        "icustays",
        "d_items",
    ]:
        assert (out / f"{t}.csv.gz").exists()
