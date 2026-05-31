"""Smoke tests for the MIMIC-CXR report-correction benchmark
(``xray_report_correction``).

These exercise the benchmark-specific helpers that we control end-to-end:
report-section parsing, eligibility filtering math, the Harbor task
generator (layout only), the pooled-metric aggregator, and the verifier
contract. They do NOT invoke PhysioNet, Docker, CheXprompt, or a real
agent — those live in integration tests run separately.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts" / "xray_report_correction"
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

def test_curated_manifest_shape_and_swap_rules():
    """Audit each committed task manifest under tasks/xray_report_correction/:
    it must carry the swap-rule list (not the legacy
    ``counterfactual_findings`` string), reference one is_target study,
    and only expose hashed IDs (no raw MIMIC subject/study IDs)."""
    tasks_root = REPO_ROOT / "tasks" / "xray_report_correction"
    case_dirs = sorted(p for p in tasks_root.glob("case_*") if p.is_dir())
    assert case_dirs, "no case_* dirs found — did you run the generator?"
    for case_dir in case_dirs:
        manifest_path = case_dir / "environment" / "task_manifest.json"
        manifest = json.loads(manifest_path.read_text())

        # Shape the bootstrap relies on.
        assert "subject_id" in manifest
        assert "target_study_id" in manifest
        assert manifest["studies"], f"{case_dir.name} has no studies"
        targets = [s for s in manifest["studies"] if s.get("is_target")]
        assert len(targets) == 1, f"{case_dir.name} must have exactly one target"

        # Swap rules — replaces the legacy ``counterfactual_findings`` string.
        rules = manifest.get("counterfactual_swap_rules")
        assert rules, f"{case_dir.name} missing counterfactual_swap_rules"
        assert all(isinstance(r, list) and len(r) == 2 for r in rules), (
            f"{case_dir.name} rules must be [src, dst] pairs"
        )
        assert "counterfactual_findings" not in manifest, (
            f"{case_dir.name} still carries legacy counterfactual_findings"
        )

        # De-id contract: hashed IDs are hex digests (no raw MIMIC ``p\\d{8}``).
        assert not manifest["subject_id"].startswith("p"), (
            f"{case_dir.name} leaks raw subject_id"
        )
        for s in manifest["studies"]:
            assert not s["study_id"].startswith("s"), (
                f"{case_dir.name} leaks raw study_id"
            )


# ---------------------------------------------------------------------------
# aggregate_metric.py — pooled CheXprompt pass-rate aggregator
# ---------------------------------------------------------------------------

def _write_trial_reward(run_dir: Path, trial_name: str, payload: dict) -> None:
    """Drop a reward.json into ``run_dir/<trial>/verifier/`` so the
    aggregator's trial-scan code path picks it up."""
    vd = run_dir / trial_name / "verifier"
    vd.mkdir(parents=True, exist_ok=True)
    (vd / "reward.json").write_text(json.dumps(payload))


def test_aggregate_metric_pools_pass_rate_and_mean_sig_errors(tmp_path):
    """Two passing + one failing trial -> reward = 2/3, success = 2, n_trials = 3.
    mean_sig_errors should average across only the trials that reported it."""
    import importlib
    agg = importlib.import_module("aggregate_metric")

    run_dir = tmp_path / "job__model__ts"
    _write_trial_reward(run_dir, "case_01__aaa",
        {"reward": 1.0, "n_tasks": 1, "n_pass": 1, "pass_rate": 1.0, "mean_sig_errors": 0.0})
    _write_trial_reward(run_dir, "case_02__bbb",
        {"reward": 1.0, "n_tasks": 1, "n_pass": 1, "pass_rate": 1.0, "mean_sig_errors": 0.4})
    _write_trial_reward(run_dir, "case_03__ccc",
        {"reward": 0.0, "n_tasks": 1, "n_pass": 0, "pass_rate": 0.0, "mean_sig_errors": 2.0})

    output_path = tmp_path / "metric.json"
    # main() takes (input_path, output_path); input.parent is the run dir.
    agg.main(run_dir / "rewards.jsonl", output_path)

    data = json.loads(output_path.read_text())
    assert data["n_trials"] == 3
    assert data["success"] == 2
    assert data["reward"] == pytest.approx(2 / 3)
    assert data["mean_pass_rate"] == pytest.approx(2 / 3)
    assert data["mean_sig_errors"] == pytest.approx((0.0 + 0.4 + 2.0) / 3)
    assert data["n_failed"] == 0


def test_aggregate_metric_synthesizes_zero_reward_for_crashed_trials(tmp_path):
    """A trial dir with exception.txt but no reward.json must count against
    pass rate (synthetic 0 reward) and bump n_failed. mean_sig_errors must
    skip the synthetic row so the diagnostic isn't biased downward."""
    import importlib
    agg = importlib.import_module("aggregate_metric")

    run_dir = tmp_path / "job__model__ts"
    # 1 real pass with sig_errors=1.0
    _write_trial_reward(run_dir, "case_01__aaa",
        {"reward": 1.0, "n_tasks": 1, "n_pass": 1, "pass_rate": 1.0, "mean_sig_errors": 1.0})
    # 1 crashed trial: exception.txt present, no reward.json
    crashed = run_dir / "case_02__bbb"
    crashed.mkdir(parents=True)
    (crashed / "exception.txt").write_text("AgentTimeoutError")

    output_path = tmp_path / "metric.json"
    agg.main(run_dir / "rewards.jsonl", output_path)

    data = json.loads(output_path.read_text())
    assert data["n_trials"] == 2
    assert data["success"] == 1
    assert data["reward"] == pytest.approx(0.5)
    assert data["n_failed"] == 1
    # mean_sig_errors averages only over rows that actually scored
    assert data["mean_sig_errors"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Verifier contract — exercised without a running container
# ---------------------------------------------------------------------------

def test_evaluate_submission_omits_mean_sig_errors_for_empty_submission():
    """Regression guard: an empty submission must score reward=0 and
    pass_rate=0, but ``mean_sig_errors`` must be omitted (None) — it
    didn't actually score 0 CheXprompt errors, it didn't score at all.
    Leaving the diagnostic key out keeps the trial-level metric honest
    when aggregated alongside real CheXprompt runs.
    """
    import importlib
    evaluator = importlib.import_module("harbor_evaluator")

    submission = [{"task_id": "case_01", "final_answer": ""}]
    answer_key = [
        {"task_id": "case_01", "study_id": "h0001", "expected_findings": "Lungs are clear."}
    ]
    out = evaluator.evaluate_submission_rows(submission, answer_key)

    assert out["reward"] == 0.0
    assert out["n_pass"] == 0
    assert out["pass_rate"] == 0.0
    # mean_sig_errors must be None (not 0.0) so reward.json omits the key.
    assert out["mean_sig_errors"] is None
    # The per-row diagnostic should explain WHY we scored 0.
    assert len(out["results"]) == 1
    assert out["results"][0]["match"] is False
    assert out["results"][0]["error"] == "empty candidate findings"


def test_extract_findings_strips_outer_sections_and_keeps_findings_only():
    """harbor_evaluator._extract_findings should isolate the FINDINGS body
    even when the submission carries adjacent EXAMINATION / IMPRESSION
    headers — CheXprompt scores FINDINGS only."""
    import importlib
    evaluator = importlib.import_module("harbor_evaluator")

    pred_with_junk = (
        "FINAL REPORT\n"
        "EXAMINATION: stuff\n\n"
        "FINDINGS:\n  lungs are clear.\n\n"
        "IMPRESSION:\n  no acute findings."
    )
    findings = evaluator._extract_findings(pred_with_junk)
    assert "lungs are clear" in findings
    assert "IMPRESSION" not in findings
    assert "EXAMINATION" not in findings


# ---------------------------------------------------------------------------
# Verifier surfaces a clear error when the bootstrap-staged gold is absent.
# Workflow §7 ("for adapted benchmarks that require agent-run setup, include
# at least one test that proves the verifier fails when the expected setup
# artifacts are missing"). Here the "setup artifact" is the gold report that
# the bootstrap compose service writes to /tests/target_report.txt before
# main starts — without it the trial cannot be scored.
# ---------------------------------------------------------------------------

def test_bootstrap_gold_raises_when_target_report_missing(tmp_path):
    import importlib
    vmt = importlib.import_module("verify_meta_task")
    answer_key = [{"task_id": "case_01", "expected_findings": ""}]
    logs_dir = tmp_path / "logs"; logs_dir.mkdir()
    with pytest.raises(vmt.MissingGoldError):
        vmt._bootstrap_gold(
            answer_key,
            answer_key_path=tmp_path / "task_answer_key.json",
            logs_dir=logs_dir,
            target_report_path=tmp_path / "absent.txt",
        )


def test_bootstrap_gold_raises_when_target_report_has_no_findings(tmp_path):
    import importlib
    vmt = importlib.import_module("verify_meta_task")
    target = tmp_path / "target_report.txt"
    target.write_text("EXAMINATION: chest\nIMPRESSION: stable.\n")
    answer_key = [{"task_id": "case_01", "expected_findings": ""}]
    logs_dir = tmp_path / "logs"; logs_dir.mkdir()
    with pytest.raises(vmt.MissingGoldError, match="no FINDINGS"):
        vmt._bootstrap_gold(
            answer_key,
            answer_key_path=tmp_path / "task_answer_key.json",
            logs_dir=logs_dir,
            target_report_path=target,
        )


def test_bootstrap_gold_injects_findings_and_impression_from_staged_report(tmp_path):
    import importlib
    vmt = importlib.import_module("verify_meta_task")
    target = tmp_path / "target_report.txt"
    target.write_text(
        "EXAMINATION: chest\n\n"
        "FINDINGS:\nLungs are clear.\n\n"
        "IMPRESSION:\nNo acute findings.\n"
    )
    answer_key = [{"task_id": "case_01", "expected_findings": ""}]
    logs_dir = tmp_path / "logs"; logs_dir.mkdir()
    vmt._bootstrap_gold(
        answer_key,
        answer_key_path=tmp_path / "task_answer_key.json",
        logs_dir=logs_dir,
        target_report_path=target,
    )
    assert answer_key[0]["expected_findings"] == "Lungs are clear."
    assert answer_key[0]["expected_impression"] == "No acute findings."
