"""Tests for scripts/ct_abnormality/gold_derivation.py.

Two layers:
- offline unit tests on synthetic report text exercising the phrase logic
  (present-only -> 1, absent-only -> 0, conflict/silence -> drop);
- an HF-gated integration test that downloads the real CT-RATE validation
  reports and asserts the runtime derivation reproduces the committed
  expected-gold snapshot for all 10 benchmark volumes. It is skipped when no
  Hugging Face token is available (offline / CI without creds).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "ct_abnormality"))

from gold_derivation import (  # noqa: E402
    FINDINGS,
    PHRASES,
    derive_finding,
    derive_volume_gold,
)

EXPECTED_GOLD = REPO_ROOT / "tests" / "data" / "ct_abnormality_expected_gold.json"
REPORTS_REPO = "ibrahimhamamci/CT-RATE"
REPORTS_PATH = "dataset/radiology_text_reports/validation_reports.csv"
SILVER_PATH = "dataset/multi_abnormality_labels/valid_predicted_labels.csv"


# --------------------------------------------------------------------------
# Offline unit tests (synthetic report text)
# --------------------------------------------------------------------------


def test_phrases_cover_all_evaluated_findings() -> None:
    assert set(PHRASES) == set(FINDINGS)
    assert len(FINDINGS) == 17
    assert "Pulmonary fibrotic sequela" not in FINDINGS


def test_present_only_is_one() -> None:
    assert derive_finding("Hiatal hernia", "There is a sliding type hiatal hernia.") == 1
    assert derive_finding("Cardiomegaly", "The heart is larger than normal.") == 1


def test_absent_only_is_zero() -> None:
    assert derive_finding("Cardiomegaly", "Heart contour and size are normal.") == 0
    assert derive_finding("Lymphadenopathy", "No enlarged lymph nodes were detected.") == 0


def test_conflict_is_dropped() -> None:
    # Effusion present on the right but explicitly absent on the left -> drop.
    text = (
        "An effusion measuring 31 mm was observed between the pleural leaves on the right. "
        "No pleural effusion was detected on the left."
    )
    assert derive_finding("Pleural effusion", text) is None


def test_silence_is_dropped() -> None:
    assert derive_finding("Bronchiectasis", "The study is technically adequate.") is None


def test_present_phrase_is_negation_guarded() -> None:
    # A finding-name present phrase must NOT fire inside a negated clause.
    assert derive_finding("Hiatal hernia", "There is no hiatal hernia.") is None
    assert derive_finding("Hiatal hernia", "No evidence of hiatal hernia.") is None
    assert derive_finding("Hiatal hernia", "There is a hiatal hernia.") == 1
    assert derive_finding("Bronchiectasis", "There is no bronchiectasis.") is None
    assert derive_finding("Bronchiectasis", "Minimal bronchiectasis is observed.") == 1
    # A negation about an earlier finding (other clause) must not bleed across.
    assert derive_finding("Hiatal hernia", "No emphysema. There is a hiatal hernia.") == 1


def test_pericardial_does_not_leak_into_pleural() -> None:
    # "pericardial effusion ... not detected" must NOT make Pleural effusion fire.
    text = "Pericardial effusion was not detected."
    assert derive_finding("Pleural effusion", text) is None
    assert derive_finding("Pericardial effusion", text) == 0


def test_atheroma_without_calcified_is_not_calcification() -> None:
    text = "Atheroma plaques were observed in the aorta and coronary arteries."
    assert derive_finding("Arterial wall calcification", text) is None
    assert derive_finding("Coronary artery wall calcification", text) is None


def test_derive_volume_gold_orders_and_filters() -> None:
    text = (
        "There is a hiatal hernia. Heart contour and size are normal. "
        "The study is otherwise unremarkable."
    )
    labels = derive_volume_gold(text)
    names = [lab["name"] for lab in labels]
    assert names == ["Cardiomegaly", "Hiatal hernia"]  # FINDINGS order, filtered
    by = {lab["name"]: lab["gold"] for lab in labels}
    assert by == {"Cardiomegaly": 0, "Hiatal hernia": 1}


# --------------------------------------------------------------------------
# HF-gated integration test (real reports)
# --------------------------------------------------------------------------


def _hf_token() -> str | None:
    tok = os.environ.get("HF_TOKEN", "").strip()
    if tok:
        return tok
    cache = Path.home() / ".cache" / "huggingface" / "token"
    if cache.exists():
        return cache.read_text().strip() or None
    return None


def _download(path: str, tmp_path: Path) -> Path:
    from huggingface_hub import hf_hub_download  # local import; only when token present

    return Path(
        hf_hub_download(
            REPORTS_REPO, path, repo_type="dataset", token=_hf_token(), local_dir=str(tmp_path)
        )
    )


def _load_silver(csv_path: Path) -> dict[str, dict[str, int]]:
    import csv as _csv

    out: dict[str, dict[str, int]] = {}
    with csv_path.open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            out[row["VolumeName"]] = {k: int(v) for k, v in row.items() if k != "VolumeName"}
    return out


@pytest.mark.skipif(_hf_token() is None, reason="no Hugging Face token; gated download unavailable")
def test_runtime_derivation_matches_silver_labels(tmp_path: Path) -> None:
    """Core correctness invariant: for every label the rules *retain*, the
    derived polarity must equal CT-RATE's silver label. The rules only filter
    out ambiguous findings (drop) — they never flip a value relative to silver.
    """
    from gold_derivation import load_report_text  # noqa: E402

    reports = _download(REPORTS_PATH, tmp_path)
    silver = _load_silver(_download(SILVER_PATH, tmp_path))
    expected = json.loads(EXPECTED_GOLD.read_text())

    for task_id in expected:
        volume = f"{task_id}.nii.gz"
        derived = derive_volume_gold(load_report_text(reports, volume))
        sv = silver[volume]
        for lab in derived:
            assert lab["gold"] == sv[lab["name"]], (
                f"{task_id}/{lab['name']}: derived {lab['gold']} != silver {sv[lab['name']]}"
            )


@pytest.mark.skipif(_hf_token() is None, reason="no Hugging Face token; gated download unavailable")
def test_runtime_derivation_matches_expected_snapshot(tmp_path: Path) -> None:
    """The retained label *set* (which findings survive filtering) is stable
    against the committed snapshot — guards accidental rule drift."""
    from gold_derivation import load_report_text  # noqa: E402

    reports = _download(REPORTS_PATH, tmp_path)
    expected = json.loads(EXPECTED_GOLD.read_text())
    for task_id, exp_labels in expected.items():
        volume = f"{task_id}.nii.gz"
        derived = {
            lab["name"]: lab["gold"]
            for lab in derive_volume_gold(load_report_text(reports, volume))
        }
        assert derived == exp_labels, f"{task_id}: derived {derived} != expected {exp_labels}"
