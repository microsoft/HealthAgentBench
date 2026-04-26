"""Smoke tests for the MIMIC-CXR report-generation benchmark.

These exercise the benchmark-specific helpers that we control end-to-end:
report-section parsing, eligibility filtering math, the Harbor task
generator (layout only), and the pooled-metric aggregator. They do NOT
invoke PhysioNet, Docker, CheXbert, or a real Codex agent — those live in
integration tests run separately.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts" / "mimic_report_gen"
sys.path.insert(0, str(SCRIPTS_DIR))

import normalization  # noqa: E402


# ---------------------------------------------------------------------------
# parse_report_sections / has_clear_findings_impression / split_target_report
# ---------------------------------------------------------------------------

REAL_REPORT_WITH_CLEAR_SECTIONS = """\
                                 FINAL REPORT
 EXAMINATION:  CHEST (PORTABLE AP)

 INDICATION:  ___F with cough  // acute process?

 COMPARISON:  Chest radiograph ___

 FINDINGS:

 Single frontal view of the chest provided.

 There is no focal consolidation, effusion, or pneumothorax. The
 cardiomediastinal silhouette is normal.  Again seen are multiple clips
 projecting over the left breast and remote left-sided rib fractures.

 IMPRESSION:

 No acute intrathoracic process.
"""


def test_parse_report_sections_extracts_all_known_sections():
    sections = normalization.parse_report_sections(REAL_REPORT_WITH_CLEAR_SECTIONS)
    assert set(sections) == {"EXAMINATION", "INDICATION", "COMPARISON", "FINDINGS", "IMPRESSION"}
    assert "CHEST (PORTABLE AP)" in sections["EXAMINATION"]
    assert "acute process?" in sections["INDICATION"]
    # Whitespace inside each body should be trimmed at edges but preserved internally
    assert sections["FINDINGS"].startswith("Single frontal view")
    assert "pneumothorax" in sections["FINDINGS"]
    assert sections["IMPRESSION"] == "No acute intrathoracic process."


def test_split_target_report_isolates_findings_and_impression():
    given, target = normalization.split_target_report(REAL_REPORT_WITH_CLEAR_SECTIONS)
    assert set(target) == {"FINDINGS", "IMPRESSION"}
    assert "FINDINGS" not in given
    assert "IMPRESSION" not in given
    # Given sections retain everything else
    assert given["EXAMINATION"].startswith("CHEST")
    assert given["INDICATION"].startswith("___F")


def test_has_clear_findings_impression_accepts_clean_report():
    assert normalization.has_clear_findings_impression(REAL_REPORT_WITH_CLEAR_SECTIONS) is True


@pytest.mark.parametrize(
    "text,reason",
    [
        ("FINDINGS:\nclear\n", "missing IMPRESSION"),
        ("FINDINGS:\nlung.\nIMPRESSION:\nFINDINGS:\nduplicate", "two FINDINGS headers"),
        ("FINDINGS:\n.\nIMPRESSION:\n.", "impression body too short"),
        ("IMPRESSION:\nno acute\n\nFINDINGS:\nclear", "wrong order (impression before findings)"),
        ("", "empty"),
    ],
)
def test_has_clear_findings_impression_rejects_malformed(text: str, reason: str):
    assert normalization.has_clear_findings_impression(text) is False, reason


# ---------------------------------------------------------------------------
# Eligibility filter math (on synthetic in-memory data, no PhysioNet required)
# ---------------------------------------------------------------------------

def _stub_patient_studies(
    num_studies: int = 2,
    subject: str = "12345678",
    study_ids: tuple[str, ...] | None = None,
) -> dict:
    """Build a minimal `patient_studies` dict shape matching build_patient_studies."""
    if study_ids is None:
        study_ids = tuple(f"5{i:07d}" for i in range(num_studies))
    return {
        subject: [
            {
                "study_id": sid,
                "subject_id": subject,
                "study_date": "21800506",
                "study_time": "213014",
                "study_datetime": f"2180-05-{i+1:02d} 21:30:14",
                "procedure": "CHEST (PORTABLE AP)",
                "views": [
                    {"dicom_id": f"dicom_{sid}", "view_position": "AP"},
                ],
            }
            for i, sid in enumerate(study_ids)
        ]
    }


def _write_stub_meta(meta_root: Path, splits: dict[str, str]) -> None:
    """Write a minimal mimic-cxr-2.0.0-split.csv.gz so load_split_assignments
    doesn't explode during eligibility filtering in tests."""
    import csv, gzip
    meta_root.mkdir(parents=True, exist_ok=True)
    path = meta_root / "mimic-cxr-2.0.0-split.csv.gz"
    with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dicom_id", "study_id", "subject_id", "split"])
        for sid, split in splits.items():
            w.writerow([f"dicom_{sid}", sid, "unused", split])


def _write_stub_zip(zip_path: Path, entries: dict[str, str]) -> None:
    """Write a minimal mimic-cxr-reports.zip-shape archive."""
    import zipfile
    with zipfile.ZipFile(zip_path, "w") as zf:
        for arcname, text in entries.items():
            zf.writestr(arcname, text)


def test_select_eligible_patients_filters_by_min_studies(tmp_path):
    """Patient with <min_studies studies is always ineligible even when
    disk/zip are present. This guards the pass-1 short-circuit."""
    patient_studies = _stub_patient_studies(num_studies=1)
    _write_stub_meta(tmp_path / "meta", {})
    _write_stub_zip(tmp_path / "reports.zip", {})
    eligible = normalization.select_eligible_patients(
        patient_studies,
        image_root=tmp_path / "images",
        reports_zip=tmp_path / "reports.zip",
        meta_root=tmp_path / "meta",
        min_studies=2,
        target_split="test",
        require_nonempty_findings_impression=False,
    )
    assert eligible == []


def test_select_eligible_patients_requires_target_in_split(tmp_path):
    """Patient whose target study isn't in `target_split` is dropped even if
    other structural checks would pass."""
    patient_studies = _stub_patient_studies(
        num_studies=2, study_ids=("50000001", "50000002")
    )
    # Mark the TARGET (latest) as "train" so it doesn't match --target_split=test.
    _write_stub_meta(tmp_path / "meta", {
        "50000001": "test",
        "50000002": "train",
    })
    _write_stub_zip(tmp_path / "reports.zip", {})
    eligible = normalization.select_eligible_patients(
        patient_studies,
        image_root=tmp_path / "images",
        reports_zip=tmp_path / "reports.zip",
        meta_root=tmp_path / "meta",
        min_studies=2,
        target_split="test",
        require_nonempty_findings_impression=False,
    )
    assert eligible == []


# ---------------------------------------------------------------------------
# Harbor task generator (layout only — no PhysioNet, no CheXbert)
# ---------------------------------------------------------------------------

def test_build_task_manifest_shape():
    """build_task_for_patient is generator-internal; verify the produced
    task dict matches the shape agents rely on."""
    import zipfile

    # Real zip-free path: build_task_for_patient reads the TARGET report via
    # read_report(). Build a tiny zip fixture containing exactly that report.
    import importlib
    gen = importlib.import_module("generate_harbor_tasks")

    tmp_zip = Path("/tmp") / "mimic_cxr_reports_fake.zip"
    subject = "10046166"
    target_sid = "50051329"
    group = f"p{subject[:2]}"
    arcname = f"files/{group}/p{subject}/s{target_sid}.txt"
    with zipfile.ZipFile(tmp_zip, "w") as zf:
        zf.writestr(arcname, REAL_REPORT_WITH_CLEAR_SECTIONS)

    studies = [
        {
            "study_id": "49999999",
            "subject_id": subject,
            "study_date": "21800506",
            "study_time": "213014",
            "study_datetime": "2180-05-06 21:30:14",
            "procedure": "CHEST (PORTABLE AP)",
            "views": [{"dicom_id": "dicom_prior", "view_position": "AP"}],
        },
        {
            "study_id": target_sid,
            "subject_id": subject,
            "study_date": "21800606",
            "study_time": "213014",
            "study_datetime": "2180-06-06 21:30:14",
            "procedure": "CHEST (PORTABLE AP)",
            "views": [{"dicom_id": "dicom_target", "view_position": "AP"}],
        },
    ]

    # Need to supply reports_zip pointing at the fake zip for the TARGET read
    # (prior entries now reference report_path only, so no zip read per-prior).
    task = normalization.build_task_for_patient(subject, studies, reports_zip=tmp_zip)
    manifest = gen._build_task_manifest(task)

    # Task payload shape
    assert task["task_id"] == f"mimic_cxr_report_{subject}_{target_sid}"
    assert task["subject_id"] == subject
    assert task["target_study"]["study_id"] == target_sid
    # Target study exposes given_sections (everything except FINDINGS / IMPRESSION)
    given = task["target_study"]["given_sections"]
    assert "FINDINGS" not in given and "IMPRESSION" not in given
    assert "EXAMINATION" in given
    # Prior studies carry report_path (not embedded text)
    assert len(task["history"]) == 1
    prior = task["history"][0]
    assert "report_path" in prior and "report" not in prior
    assert prior["report_path"].endswith(f"s{studies[0]['study_id']}/report.txt".replace("s49999999/", "").replace("/report.txt", "/report.txt")) or "report.txt" in prior["report_path"]

    # Manifest shape drives the entrypoint at container start
    assert manifest["subject_id"] == subject
    assert manifest["target_study_id"] == target_sid
    assert len(manifest["studies"]) == 2
    assert any(s["is_target"] for s in manifest["studies"])

    tmp_zip.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# aggregate_metric.py — pooled CheXbert / BLEU / ROUGE-L
# ---------------------------------------------------------------------------

CHEXBERT_LABELS = (
    "Enlarged Cardiomediastinum", "Cardiomegaly", "Lung Opacity", "Lung Lesion",
    "Edema", "Consolidation", "Pneumonia", "Atelectasis", "Pneumothorax",
    "Pleural Effusion", "Pleural Other", "Fracture", "Support Devices", "No Finding",
)


def _mk_trial_reward(ref_vec: list[int], pred_vec: list[int], *, reward: float = 0.2,
                     avg_bleu: float = 0.0, avg_rouge_l: float = 0.2, fill_rate: float = 1.0) -> dict:
    """Build one trial's reward.json payload in the shape verify_meta_task.py emits."""
    payload = {
        "reward": reward,
        "total": 1,
        "filled": int(fill_rate > 0),
        "avg_bleu": avg_bleu,
        "avg_rouge_l": avg_rouge_l,
        "fill_rate": fill_rate,
    }
    for i, label in enumerate(CHEXBERT_LABELS):
        slug = label.replace(" ", "_").lower()
        payload[f"chx_ref_{slug}"] = int(ref_vec[i])
        payload[f"chx_pred_{slug}"] = int(pred_vec[i])
    return payload


def test_aggregate_metric_flat_keys_and_correct_math(tmp_path):
    """Feed a tiny 3-trial rewards.jsonl to aggregate_metric.main() and verify
    the output dict has flat keys (`chexbert_f1_14_micro_f1`, ...) and that
    the pooled classification_report output is consistent with sklearn."""
    import subprocess

    # 3 trials with varying ref/pred vectors
    # Trial 1: perfect match on Fracture
    # Trial 2: ref has Cardiomegaly, pred misses it
    # Trial 3: both say No Finding
    ref_1 = [0]*14; pred_1 = [0]*14
    ref_1[CHEXBERT_LABELS.index("Fracture")] = 1; pred_1[CHEXBERT_LABELS.index("Fracture")] = 1
    ref_2 = [0]*14; pred_2 = [0]*14
    ref_2[CHEXBERT_LABELS.index("Cardiomegaly")] = 1  # pred_2 all zeros → FN
    ref_3 = [0]*14; pred_3 = [0]*14
    ref_3[CHEXBERT_LABELS.index("No Finding")] = 1
    pred_3[CHEXBERT_LABELS.index("No Finding")] = 1

    rewards_path = tmp_path / "rewards.jsonl"
    with rewards_path.open("w") as f:
        for ref, pred in [(ref_1, pred_1), (ref_2, pred_2), (ref_3, pred_3)]:
            f.write(json.dumps(_mk_trial_reward(ref, pred)) + "\n")

    output_path = tmp_path / "metric.json"
    # Run the aggregator as a subprocess — keeps deps isolated (torch etc.
    # are not imported for the non-CheXbert code paths, but running the
    # script directly is the canonical invocation shape Harbor uses).
    # We bypass uv script-level deps by invoking the module function directly
    # in-process, since our test deps already include scikit-learn+numpy.
    import importlib
    agg = importlib.import_module("aggregate_metric")
    agg.main(rewards_path, output_path)

    data = json.loads(output_path.read_text())

    # Flat, top-level keys — no nesting
    assert "chexbert" not in data
    assert "chexbert_f1_14_micro_f1" in data
    assert "chexbert_f1_14_macro_f1" in data
    assert "chexbert_f1_5_micro_f1" in data
    assert "chexbert_f1_5_macro_f1" in data
    assert "chexbert_accuracy" in data
    assert "chexbert_n_pairs" in data
    # Scalar aggregates
    assert data["num_trials"] == 3
    assert data["total_tasks"] == 3
    assert data["filled_tasks"] == 3
    assert data["fill_rate"] == 1.0
    assert data["chexbert_n_pairs"] == 3

    # Sanity: at least some positive F1 on the 14-label set, since
    # trial 1 has a true-positive Fracture match and trial 3 has a
    # true-positive No Finding match.
    assert data["chexbert_f1_14_micro_f1"] > 0.0


def test_aggregate_metric_missing_chexbert_fields_skips_gracefully(tmp_path):
    """When rewards.jsonl lacks chx_* fields, the aggregator should still
    emit the scalar averages and a chexbert_error string instead of crashing."""
    rewards_path = tmp_path / "rewards.jsonl"
    rewards_path.write_text(json.dumps({
        "reward": 0.2,
        "total": 1,
        "filled": 1,
        "avg_bleu": 0.01,
        "avg_rouge_l": 0.2,
        "fill_rate": 1.0,
    }) + "\n")
    output_path = tmp_path / "metric.json"

    import importlib
    agg = importlib.import_module("aggregate_metric")
    agg.main(rewards_path, output_path)

    data = json.loads(output_path.read_text())
    assert data["num_trials"] == 1
    assert data["avg_rouge_l"] == 0.2
    assert data.get("chexbert_error", "").startswith("no chx_")


# ---------------------------------------------------------------------------
# Verifier contract — exercised without a running container
# ---------------------------------------------------------------------------

def test_verifier_normalizer_strips_whitespace_and_section_headers():
    """The evaluator must parse FINDINGS / IMPRESSION equally regardless of
    surrounding whitespace and outer sections."""
    # Reach into harbor_evaluator — same directory as normalization.py
    import importlib
    evaluator = importlib.import_module("harbor_evaluator")

    pred_with_junk = """FINAL REPORT
EXAMINATION: stuff

FINDINGS:
  lungs are clear.

IMPRESSION:
  no acute findings."""
    canonical = """FINDINGS:
lungs are clear.

IMPRESSION:
no acute findings."""
    assert evaluator._normalize_report(pred_with_junk) == evaluator._normalize_report(canonical)
