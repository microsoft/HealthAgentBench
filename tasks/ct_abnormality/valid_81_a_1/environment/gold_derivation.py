"""Runtime gold derivation for the ct_abnormality benchmark.

The benchmark's gold labels are **not** stored in the repo. Instead, this module
re-derives them at task-bootstrap time from the volume's paired CT-RATE radiology
report, using a hardcoded set of unambiguous report phrases. Keeping only the
phrase rules in git (not the reports or the answer key) avoids redistributing the
gated CT-RATE text while keeping the task fully reproducible: each task container
downloads its own report on first run and derives its own gold.

Derivation model
----------------
For each of the 17 evaluated abnormality findings, we hold two lists of
**long, unambiguous phrases** taken from radiology-report language:

- ``present`` phrases — their appearance means the finding is present (gold 1).
- ``absent`` phrases — their appearance means the finding is explicitly negated
  (gold 0).

A finding's gold for a given report is then:

- ``1`` if some ``present`` phrase matches and no ``absent`` phrase matches,
- ``0`` if some ``absent`` phrase matches and no ``present`` phrase matches,
- *dropped* (not scored) if **both** match (an intra-report conflict, e.g. an
  effusion present on one side but absent on the other) or if **neither** matches
  (the report does not address the finding unambiguously).

This "conflict or silence -> drop" rule is what keeps the scored label set tight:
only findings the report speaks to unambiguously are retained. Phrases are matched
case-insensitively as substrings of ``Findings_EN`` + ``Impressions_EN``.

The phrase lists are intentionally specific (often multi-word clinical
statements) so a phrase cannot fire for the wrong finding — e.g. bare
``"effusion"`` would match *pericardial* effusion, so ``Pleural effusion`` instead
keys on ``"between the pleural leaves"`` / ``"no pleural or pericardial effusion"``.

CLI (used by the task bootstrap)
--------------------------------
    python gold_derivation.py \
        --reports-csv /data/_cache/validation_reports.csv \
        --volume valid_670_a_1.nii.gz \
        --out-gold /tests/gold.json \
        --out-labels /workspace/data/labels.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# The 17 evaluated CT-RATE abnormality categories. (The 18th, "Pulmonary
# fibrotic sequela", is intentionally excluded from the benchmark.) Order here
# is the canonical order labels are emitted in.
FINDINGS: list[str] = [
    "Medical material",
    "Arterial wall calcification",
    "Cardiomegaly",
    "Pericardial effusion",
    "Coronary artery wall calcification",
    "Hiatal hernia",
    "Lymphadenopathy",
    "Emphysema",
    "Atelectasis",
    "Lung nodule",
    "Lung opacity",
    "Pleural effusion",
    "Mosaic attenuation pattern",
    "Peribronchial thickening",
    "Consolidation",
    "Bronchiectasis",
    "Interlobular septal thickening",
]

# finding -> {"present": [...], "absent": [...]} unambiguous report phrases.
#
# Phrases are LONG (multi-word clinical statements / near-full sentences), taken
# verbatim from CT-RATE report language, so each key is unambiguous on its own
# and cannot fire for the wrong finding or under a negation. Matching is a
# lowercased substring test (present phrases are additionally negation-guarded;
# see ``_present_unnegated``). See the module docstring for the derivation
# semantics (present-only -> 1, absent-only -> 0, both/neither -> drop).
#
# Design notes on deliberately-dropped (ambiguous) cases:
#   * "atheroma plaques" / "atherosclerotic changes" WITHOUT "calcified" are not
#     unambiguous evidence of *wall calcification*, so the calcification findings
#     require the word "calcified" — atheroma-only reports are dropped (not
#     scored), which does not contradict the silver label, it just abstains.
#   * a finding that is present on one side but explicitly absent on the other
#     (e.g. valid_144 pleural effusion) matches both lists -> conflict -> drop.
PHRASES: dict[str, dict[str, list[str]]] = {
    "Medical material": {
        "present": ["stent in the aortic", "stent material"],
        "absent": [],
    },
    "Arterial wall calcification": {
        # Require explicit *calcified* aortic/arterial wall disease ("atheroma"
        # / "atherosclerotic changes" without "calcified" is ambiguous -> drop).
        "present": ["calcified atherosclerotic changes in the thoracic aorta"],
        "absent": [],
    },
    "Cardiomegaly": {
        # NB: "CTO increased in favor of the heart" is NOT treated as cardiomegaly
        # (indirect/ambiguous) — only an explicitly enlarged heart counts.
        "present": [
            "heart is larger than normal",
            "heart size increased",
        ],
        "absent": [
            "heart contour, size are normal",
            "heart contour and size are normal",
            "heart dimensions and compartments appear natural",
            "vascular structures have a natural appearance",
        ],
    },
    "Pericardial effusion": {
        "present": ["pericardial thickening-effusion"],
        "absent": [
            "pericardial effusion was not detected",
            "pericardial effusion-thickening was not observed",
            "no pleural or pericardial effusion",
        ],
    },
    "Coronary artery wall calcification": {
        # Require *calcified* coronary-wall disease.
        "present": ["coronary artery walls", "wall of the thoracic aorta and coronary artery"],
        "absent": [],
    },
    "Hiatal hernia": {
        "present": ["hiatal hernia"],
        "absent": [],
    },
    "Lymphadenopathy": {
        "present": ["conglomerated lymphadenopathies"],
        "absent": [
            "no lymph node was observed",
            "no enlarged lymph nodes",
            "no lymph node with pathological",
            "no pathologically enlarged lymph nodes",
        ],
    },
    "Emphysema": {
        "present": ["emphysema areas", "emphysematous changes"],
        "absent": [],
    },
    "Atelectasis": {
        "present": ["linear atelectasis", "atelectatic changes"],
        "absent": [],
    },
    "Lung nodule": {
        "present": [
            "millimetric nonspecific nodules",
            "nonspecific millimetric nodules",
            "millimetric parenchymal nodules",
        ],
        "absent": ["no nodular or infiltrative lesion"],
    },
    "Lung opacity": {
        "present": ["ground glass", "ground-glass", "frosted glass", "nodular opacity"],
        "absent": [],
    },
    "Pleural effusion": {
        "present": ["between the pleural leaves"],
        "absent": [
            "no bilateral pleural effusion",
            "pleural effusion-thickening was not detected",
            "no pleural or pericardial effusion",
            "no pleural effusion was detected",
        ],
    },
    "Mosaic attenuation pattern": {
        "present": ["mosaic attenuation pattern"],
        "absent": [],
    },
    "Peribronchial thickening": {
        "present": ["peribronchial thickening"],
        "absent": [],
    },
    "Consolidation": {
        "present": [
            "nodular consolidation",
            "consolidative parenchyma",
            "consolidative areas",
            "consolidations in the converging",
            "consolidation area",
        ],
        "absent": [],
    },
    "Bronchiectasis": {
        "present": ["bronchiectasis"],
        "absent": [],
    },
    "Interlobular septal thickening": {
        "present": ["interlobular septal thickening"],
        "absent": [],
    },
}


# Negation cues that flip a "present" phrase to a non-match when they appear in
# the same clause just before it — so a present phrase like "cardiomegaly" does
# NOT fire on "no cardiomegaly" / "no evidence of cardiomegaly". (Absent phrases
# already embed their own negation and are matched verbatim.)
_NEGATION_CUES = (
    "no ",
    "not ",
    "without ",
    "free of ",
    "no evidence of ",
    "absence of ",
)
# Clause boundaries: a negation cue only suppresses a present phrase within the
# same clause, so a "no" about an earlier finding doesn't bleed across.
_CLAUSE_BOUNDARIES = (".", ";", ":", "\n")


def _present_unnegated(text: str, phrase: str) -> bool:
    """True if ``phrase`` occurs in ``text`` at least once *without* a negation
    cue earlier in the same clause (lowercased substring search)."""
    idx = 0
    while True:
        i = text.find(phrase, idx)
        if i < 0:
            return False
        boundary = max(text.rfind(b, 0, i) for b in _CLAUSE_BOUNDARIES)
        clause = text[boundary + 1 : i]
        if not any(cue in clause for cue in _NEGATION_CUES):
            return True  # an un-negated occurrence
        idx = i + len(phrase)


def _containing_sentence(report_text: str, phrase: str) -> str:
    """Return the report sentence containing ``phrase`` (verbatim, original
    case), for use as human-reviewable evidence. Falls back to the phrase."""
    low = report_text.lower()
    i = low.find(phrase)
    if i < 0:
        return phrase
    start = max(report_text.rfind(b, 0, i) for b in _CLAUSE_BOUNDARIES) + 1
    end = min(
        (e for e in (report_text.find(b, i) for b in (".", ";")) if e != -1),
        default=len(report_text),
    )
    return report_text[start : end + 1].strip()


def classify_finding(finding: str, report_text: str) -> tuple[int | None, str | None]:
    """Return ``(gold, evidence)`` for a finding.

    ``gold`` is 1/0, or None to drop (intra-report conflict or no unambiguous
    phrase). ``evidence`` is the verbatim report sentence that triggered the
    decision (None when dropped). A "present" phrase only counts if it appears
    un-negated (see :func:`_present_unnegated`); "absent" phrases are matched
    verbatim since they already encode the negation.
    """
    low = report_text.lower()
    spec = PHRASES[finding]
    pres = next((p for p in spec["present"] if _present_unnegated(low, p)), None)
    absn = next((p for p in spec["absent"] if p in low), None)
    if pres and absn:
        return None, None  # intra-report conflict -> not unambiguous -> drop
    if pres:
        return 1, _containing_sentence(report_text, pres)
    if absn:
        return 0, _containing_sentence(report_text, absn)
    return None, None  # report does not address this finding unambiguously -> drop


def derive_finding(finding: str, report_text: str) -> int | None:
    """Return 1/0 for a finding's gold, or None to drop it (conflict or silence)."""
    return classify_finding(finding, report_text)[0]


def derive_volume_gold(report_text: str) -> list[dict[str, object]]:
    """Derive the retained gold labels for one volume from its report text.

    Returns a list of ``{"name", "gold", "evidence"}`` dicts in
    :data:`FINDINGS` order, containing only the findings the report addresses
    unambiguously. ``evidence`` is the verbatim report sentence behind the call.
    """
    out: list[dict[str, object]] = []
    for finding in FINDINGS:
        gold, evidence = classify_finding(finding, report_text)
        if gold is not None:
            out.append({"name": finding, "gold": gold, "evidence": evidence})
    return out


def load_report_text(reports_csv: Path, volume_name: str) -> str:
    """Load + concatenate Findings_EN and Impressions_EN for one volume.

    ``volume_name`` is the CT-RATE volume filename (e.g. ``valid_670_a_1.nii.gz``),
    matching the report CSV's ``VolumeName`` column.
    """
    with reports_csv.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("VolumeName") == volume_name:
                findings = (row.get("Findings_EN") or "").strip()
                impressions = (row.get("Impressions_EN") or "").strip()
                return f"{findings} {impressions}".strip()
    raise KeyError(f"volume {volume_name!r} not found in {reports_csv}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-csv", type=Path, required=True)
    parser.add_argument("--volume", required=True, help="VolumeName, e.g. valid_670_a_1.nii.gz")
    parser.add_argument("--out-gold", type=Path, required=True)
    parser.add_argument("--out-labels", type=Path, required=True)
    args = parser.parse_args(argv)

    report_text = load_report_text(args.reports_csv, args.volume)
    labels = derive_volume_gold(report_text)
    if not labels:
        print(f"[gold] no unambiguous findings derived for {args.volume}", file=sys.stderr)

    gold = {"volume_name": args.volume, "labels": labels}
    args.out_gold.parent.mkdir(parents=True, exist_ok=True)
    args.out_gold.write_text(json.dumps(gold, indent=2), encoding="utf-8")

    args.out_labels.parent.mkdir(parents=True, exist_ok=True)
    args.out_labels.write_text(
        "\n".join(str(lab["name"]) for lab in labels) + ("\n" if labels else ""),
        encoding="utf-8",
    )
    print(f"[gold] {args.volume}: derived {len(labels)} labels -> {args.out_gold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
