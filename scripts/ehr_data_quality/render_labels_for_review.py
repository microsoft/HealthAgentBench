# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
# ///
"""One-off review helper: render every labeled error cluster across all four
ehr_data_quality tasks as a single markdown file so a human can audit
row-by-row whether each injected error is unambiguously genuine.

The labels.csv schema expands every injection into multiple rows: the
anchor (the corrupted row) plus zero or more evidence rows that prove the
inconsistency. Both share a ``cluster_id``. The agent only needs to flag
one row in a cluster to catch it, so we render one entry per cluster.

A suspicion flag is added based on the audit verdict for each subtype:
- "" (unflagged): unambiguous — any reasonable analyst would flag it.
- "WARN": defensible but debatable.
- "RISKY": false-positive risk; agent could miss it through reasonable
  judgment (e.g., 30-70% lab vs. bedside disagreement, or reference-range
  values indistinguishable from institutional variation).

Run:
    uv run scripts/ehr_data_quality/render_labels_for_review.py \\
        --output debug/ehr_data_quality/labels_for_review.md
"""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TASKS_ROOT = REPO_ROOT / "tasks" / "ehr_data_quality"
ASSETS_CACHE = REPO_ROOT / "scripts" / "ehr_data_quality" / "assets" / "raw_cache"


def _load_itemid_labels() -> dict[str, str]:
    """Build an ``itemid -> label`` map from MIMIC's d_labitems (lab tests)
    and d_items (chart events). Returns an empty dict if the cache is
    absent so the renderer degrades gracefully."""
    mapping: dict[str, str] = {}
    for relpath in ("hosp/d_labitems.csv.gz", "icu/d_items.csv.gz"):
        path = ASSETS_CACHE / relpath
        if not path.exists():
            continue
        try:
            with gzip.open(path, "rt") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    itemid = (row.get("itemid") or "").strip()
                    label = (row.get("label") or "").strip()
                    if itemid and label:
                        mapping[itemid] = label
        except (OSError, csv.Error):
            continue
    return mapping


ITEMID_LABELS = _load_itemid_labels()


def _format_itemid(itemid: str) -> str:
    """Render an itemid as ``Label (itemid)`` when the label is known,
    otherwise fall back to ``itemid <id>``."""
    itemid = itemid.strip()
    if not itemid:
        return ""
    label = ITEMID_LABELS.get(itemid)
    if label:
        return f"{label} ({itemid})"
    return f"itemid {itemid}"


# Suspicion verdicts grouped by the *root* subtype (i.e. stripped of the
# trailing _anchor / _evidence / _lab_evidence / _drug_evidence /
# _patient_evidence suffixes that the injector appends to context rows).
RISKY = {"cross_table_conflict", "gender_via_ref_range_swap"}
WARN = {
    "decimal_shift",
    "decimal_shift_rx",
    "unit_confusion",
    "valueuom_mismatch",
    "in_table_conflict",
}


def _root_subtype(s: str) -> str:
    """Strip evidence/anchor suffixes so 'gender_via_patients_flip_lab_evidence'
    collapses to 'gender_via_patients_flip' for verdict lookup."""
    for suf in (
        "_lab_evidence",
        "_drug_evidence",
        "_patient_evidence",
        "_evidence",
        "_anchor",
    ):
        if s.endswith(suf):
            return s[: -len(suf)]
    return s


def _verdict(subtype: str) -> tuple[str, str]:
    """Return (badge, severity) for a subtype. Badge is empty if the
    subtype is unambiguous."""
    root = _root_subtype(subtype)
    if root in RISKY:
        return "RISKY", "false-positive risk"
    if root in WARN:
        return "WARN", "defensible but debatable"
    return "", "unambiguous"


def _pick_primary(cluster_rows: pd.DataFrame) -> pd.Series:
    """Pick one row to represent a cluster in the review. Prefer the
    anchor (no _evidence suffix); fall back to the first row."""
    no_evidence = cluster_rows[
        ~cluster_rows["error_subtype"].str.contains("evidence", na=False)
    ]
    if not no_evidence.empty:
        return no_evidence.iloc[0]
    return cluster_rows.iloc[0]


# Why each marker drug is incompatible with the corruption. Used to make
# the "Contradicts" column actually explanatory rather than just naming a
# drug. Lower-cased keys; matched case-insensitively.
DRUG_INDICATION = {
    # Geriatric / dementia (incompatible with age=5)
    "donepezil": "Alzheimer's medication, geriatric-only",
    "memantine": "Alzheimer's medication, geriatric-only",
    "galantamine": "Alzheimer's medication, geriatric-only",
    "rivastigmine": "Alzheimer's medication, geriatric-only",
    # Male-marker
    "tamsulosin": "BPH (enlarged prostate) treatment, male-only",
    "finasteride": "BPH / male-pattern baldness, male-only",
    "dutasteride": "BPH treatment, male-only",
    "sildenafil": "erectile dysfunction, male-only",
    "tadalafil": "erectile dysfunction, male-only",
    "testosterone": "androgen-replacement, male-only",
    "vardenafil": "erectile dysfunction, male-only",
    # Female-marker
    "estradiol": "estrogen-replacement, female-only",
    "estrogen": "estrogen-replacement, female-only",
    "progesterone": "progestin, female-only",
    "norethindrone": "oral contraceptive, female-only",
    "levonorgestrel": "oral contraceptive, female-only",
    "drospirenone": "oral contraceptive, female-only",
    "medroxyprogesterone": "contraceptive / hormone therapy, female-only",
    "ethinyl estradiol": "oral contraceptive, female-only",
    "tamoxifen": "breast cancer (SERM), female-only",
    "anastrozole": "breast cancer aromatase inhibitor, female-only",
}


def _describe_drug(name: str) -> str:
    """Return 'DrugName (clinical-indication)' if known, else just 'DrugName'."""
    indication = DRUG_INDICATION.get(name.strip().lower())
    return f"{name} ({indication})" if indication else name


# Static descriptions for impossible_value subtypes — those "contradict"
# physiological / domain knowledge, not other rows in the data.
IMPOSSIBLE_VALUE_CONTRADICTIONS = {
    "range_extreme": (
        "Value is outside the physiologically plausible band for this lab/vital "
        "(e.g., creatinine > 20 mg/dL, glucose > 1000 mg/dL, SpO2 > 100%, "
        "negative blood pressure)."
    ),
    "decimal_shift": (
        "Value is shifted 10×, 100×, or 1000× the original — lands in the "
        "per-itemid clinically impossible band (e.g., glucose > 2000 mg/dL)."
    ),
    "decimal_shift_rx": (
        "Prescribed dose is 100× the original — well outside any reasonable "
        "dosing range for this drug."
    ),
    "unit_confusion": (
        "Value reflects a unit-conversion factor (e.g., creatinine multiplied by "
        "88.42 µmol/L conversion), but the `valueuom` column still reads the "
        "original unit — value and unit are inconsistent."
    ),
    "valueuom_mismatch": (
        "The `valueuom` column has been replaced with a unit that does not "
        "correspond to the measured value (e.g., a percentage value labeled "
        "as ng/mL)."
    ),
}


def _contradiction_summary(cluster_rows: pd.DataFrame, primary: pd.Series) -> str:
    """Build a one-cell description of what existing data in the cluster
    contradicts the corruption."""
    subtype = _root_subtype(primary["error_subtype"])

    # Impossible-value family: contradiction is domain knowledge, not
    # in-data evidence.
    if subtype in IMPOSSIBLE_VALUE_CONTRADICTIONS:
        return IMPOSSIBLE_VALUE_CONTRADICTIONS[subtype]

    # Everything else: count evidence rows by their suffix and synthesize
    # a "contradicts: X labs, Y prescriptions, Z patient row" sentence.
    evidence = cluster_rows[
        cluster_rows["error_subtype"] != primary["error_subtype"]
    ]
    if evidence.empty:
        return "_(no evidence row recorded)_"

    by_suffix: dict[str, pd.DataFrame] = {}
    for suf in ("_lab_evidence", "_drug_evidence", "_patient_evidence", "_anchor"):
        m = evidence[evidence["error_subtype"].str.endswith(suf)]
        if not m.empty:
            by_suffix[suf] = m

    # in_table_conflict / cross_table_conflict use the "_anchor" suffix to
    # point at the *other* row in the conflict pair.
    if subtype == "in_table_conflict":
        anchor = by_suffix.get("_anchor")
        if anchor is not None and not anchor.empty:
            r = anchor.iloc[0]
            return (
                f"Another row in `{r['table']}` (row_id `{r['row_id']}`) "
                f"for the same patient/time/test has `{r['field']}={r['original_value']}` "
                f"vs. corrupted `{primary['corrupted_value']}` — same conceptual "
                f"measurement, disagreeing values."
            )
    if subtype == "cross_table_conflict":
        anchor = by_suffix.get("_anchor")
        if anchor is not None and not anchor.empty:
            r = anchor.iloc[0]
            return (
                f"A row in `{r['table']}` (row_id `{r['row_id']}`) at the same "
                f"timestamp for the same patient records `{r['field']}={r['original_value']}` "
                f"vs. corrupted `{primary['corrupted_value']}` — cross-table "
                f"disagreement on the same measurement."
            )

    parts: list[str] = []

    # gender_via_prescription_swap: the *corrupted drug itself* is a gender
    # marker. Make the contradiction explicit before listing supporting
    # evidence.
    if subtype == "gender_via_prescription_swap":
        corrupted_drug = str(primary["corrupted_value"]).strip()
        pat = by_suffix.get("_patient_evidence")
        patient_gender = (
            pat.iloc[0]["original_value"] if pat is not None and not pat.empty else "?"
        )
        parts.append(
            f"Swapped-in drug {_describe_drug(corrupted_drug)} contradicts "
            f"`patients.gender = {patient_gender}`"
        )

    # Demographic / age conflicts: aggregate by suffix type.
    if "_lab_evidence" in by_suffix:
        labs = by_suffix["_lab_evidence"]
        sample_ids = (
            labs["original_value"].dropna().astype(str).unique()[:3].tolist()
            if "original_value" in labs.columns
            else []
        )
        sample_labels = [_format_itemid(i) for i in sample_ids if _format_itemid(i)]
        sample_str = f" (e.g. {', '.join(sample_labels)})" if sample_labels else ""

        # Spell out the actual contradiction mechanism per subtype. These
        # labs all have **sex-specific reference ranges** (the canonical
        # `ref_range_lower`/`ref_range_upper` band differs by sex).
        if subtype == "gender_via_patients_flip":
            parts.append(
                f"{len(labs)} of this patient's lab rows{sample_str} carry "
                f"`ref_range_lower`/`ref_range_upper` set to the canonical band for "
                f"the patient's *original* gender (`{primary['original_value']}`) "
                f"— e.g. Hemoglobin: male band 13.7–17.5 g/dL vs. female 12.0–15.5. "
                f"The flipped `patients.gender = {primary['corrupted_value']}` is "
                f"inconsistent with those reference ranges"
            )
        elif subtype == "gender_via_ref_range_swap":
            parts.append(
                f"{len(labs)} other lab row(s) for this patient{sample_str} still "
                f"carry the canonical reference-range band matching their true "
                f"gender; only this single row's `ref_range_lower`/`upper` was "
                f"overwritten to the opposite-sex band"
            )
        elif subtype == "gender_via_prescription_swap":
            parts.append(
                f"{len(labs)} of this patient's lab rows{sample_str} carry "
                f"sex-specific `ref_range` bands consistent with the patient's "
                f"true gender, contradicting the swapped-in marker drug"
            )
        else:
            parts.append(
                f"{len(labs)} sex/age-marker lab measurement(s) for this patient"
                f"{sample_str}"
            )
    if "_drug_evidence" in by_suffix:
        drugs = by_suffix["_drug_evidence"]
        sample_drugs = drugs["original_value"].dropna().astype(str).unique()[:3].tolist()
        if sample_drugs:
            described = [_describe_drug(d) for d in sample_drugs]
            # For age clusters: explicitly call out the impossibility.
            if subtype == "age_via_patients_change":
                parts.append(
                    f"{len(drugs)} prescription(s) {', '.join(described)} — "
                    f"clinically impossible for the corrupted age of "
                    f"{primary['corrupted_value']}"
                )
            else:
                parts.append(
                    f"{len(drugs)} marker prescription(s): {', '.join(described)}"
                )
        else:
            parts.append(f"{len(drugs)} marker prescription(s)")
    if "_patient_evidence" in by_suffix:
        pat = by_suffix["_patient_evidence"]
        r = pat.iloc[0]
        parts.append(
            f"`patients.gender = {r['original_value']}` for this patient"
        )

    if not parts:
        return f"_({len(evidence)} evidence row(s) of an unrecognized type)_"
    return "; ".join(parts) + "."


def _format_value(v: object) -> str:
    """Markdown-safe cell rendering for original/corrupted values."""
    if v is None:
        return "—"
    s = str(v)
    if s == "" or s.lower() == "nan":
        return "—"
    # Escape pipes so they don't break the markdown table.
    return s.replace("|", "\\|")


def render_task(task_dir: Path) -> str:
    labels = pd.read_csv(
        task_dir / "tests" / "labels.csv",
        dtype=str,
        keep_default_na=False,
    )
    task_name = task_dir.name
    cluster_groups = labels.groupby("cluster_id", sort=False)

    lines: list[str] = []
    lines.append(f"## {task_name}\n")
    lines.append(
        f"**{cluster_groups.ngroups} clusters** "
        f"(_{len(labels)} labeled rows total, including evidence_)\n"
    )

    cluster_summaries: list[dict] = []
    for cluster_id, group in cluster_groups:
        primary = _pick_primary(group)
        badge, _ = _verdict(primary["error_subtype"])
        cluster_summaries.append(
            {
                "cluster_id": cluster_id,
                "primary": primary,
                "n_rows": len(group),
                "family": primary["error_family"],
                "subtype": _root_subtype(primary["error_subtype"]),
                "badge": badge,
                "contradicts": _contradiction_summary(group, primary),
            }
        )
    cluster_summaries.sort(
        key=lambda c: (
            {"": 0, "WARN": 1, "RISKY": 2}[c["badge"]],
            c["family"],
            c["subtype"],
        )
    )

    current_family = None
    current_subtype = None
    for c in cluster_summaries:
        if c["family"] != current_family:
            current_family = c["family"]
            current_subtype = None
            lines.append(f"\n### {current_family}\n")
        if c["subtype"] != current_subtype:
            current_subtype = c["subtype"]
            verdict_badge, verdict_text = _verdict(c["subtype"])
            badge_emoji = (
                "🔴" if verdict_badge == "RISKY"
                else "🟡" if verdict_badge == "WARN"
                else "🟢"
            )
            lines.append(f"\n#### `{c['subtype']}` — {badge_emoji} {verdict_text}\n")
            lines.append(
                "| Cluster | Table | Row ID | Field | Original | Corrupted | Contradicts (in-data evidence) | Severity | Rows | Flag | Review |"
            )
            lines.append(
                "|---|---|---|---|---|---|---|---|---|---|---|"
            )
        p = c["primary"]
        flag = ""
        if c["badge"] == "RISKY":
            flag = "🚩"
        elif c["badge"] == "WARN":
            flag = "⚠️"
        contradicts = c["contradicts"].replace("|", "\\|")
        cluster_safe = c["cluster_id"].replace("|", "\\|")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{cluster_safe}`",
                    f"`{p['table']}`",
                    f"`{p['row_id']}`",
                    f"`{p['field']}`",
                    _format_value(p["original_value"]),
                    _format_value(p["corrupted_value"]),
                    contradicts,
                    p["severity"],
                    str(c["n_rows"]),
                    flag,
                    "☐",
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "debug" / "ehr_data_quality" / "labels_for_review.md",
    )
    args = parser.parse_args()

    task_dirs = sorted(d for d in TASKS_ROOT.iterdir() if d.is_dir())

    parts: list[str] = []
    parts.append("# ehr_data_quality — Injected Error Review\n")
    parts.append(
        "Every cluster across all four sub-tasks. One row per cluster "
        "(the *anchor* — the actual injected row; evidence rows are summarized "
        "by the `Rows` count). The agent only needs to flag one row per cluster "
        "to count as caught.\n\n"
        "**Flags** based on audit verdicts:\n"
        "- 🟢 (unflagged) — **unambiguous**: any reasonable EHR analyst would flag this row.\n"
        "- 🟡 ⚠️ — **defensible but debatable**: an analyst might call it suspicious but not certainly wrong.\n"
        "- 🔴 🚩 — **false-positive risk**: agent could legitimately miss it (e.g., bedside vs. lab disagreement at real-world variance levels, or reference-range overwrites indistinguishable from institutional variation).\n\n"
        "Mark the `Review` checkbox after spot-checking each cluster.\n"
    )
    for d in task_dirs:
        parts.append("\n---\n")
        parts.append(render_task(d))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
