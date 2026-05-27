"""Unit tests for the ehr_data_quality harbor_evaluator (F1 from cluster-recall + row-precision)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ehr_data_quality"))

from harbor_evaluator import evaluate  # noqa: E402


def _write_labels(path: Path, rows: list[dict[str, str]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_submission(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        pd.DataFrame(rows).to_csv(path, index=False)
    else:
        path.write_text("table,_row_id\n")


def _label_row(table: str, row_id: str, family: str, cluster_id: str,
               subtype: str | None = None) -> dict[str, str]:
    return {
        "table": table,
        "row_id": row_id,
        "error_family": family,
        "error_subtype": subtype or family,
        "field": "valuenum",
        "original_value": "1",
        "corrupted_value": "999",
        "severity": "obvious",
        "cluster_id": cluster_id,
    }


# ---------------------------------------------------------------------------
# Singleton-cluster scoring
# ---------------------------------------------------------------------------


def test_perfect_f1_when_submission_matches_labels(tmp_path: Path) -> None:
    labels = [
        _label_row("labevents", f"r{i}", "impossible_value", f"labevents|r{i}")
        for i in range(5)
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    _write_submission(
        tmp_path / "submission" / "flagged_rows.csv",
        [{"table": L["table"], "_row_id": L["row_id"]} for L in labels],
    )
    f1 = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    assert f1 == pytest.approx(1.0)
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["precision"] == pytest.approx(1.0)


def test_zero_f1_when_empty_submission(tmp_path: Path) -> None:
    labels = [
        _label_row("labevents", f"r{i}", "impossible_value", f"labevents|r{i}")
        for i in range(3)
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    _write_submission(tmp_path / "submission" / "flagged_rows.csv", [])
    f1 = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    assert f1 == 0.0


# ---------------------------------------------------------------------------
# Cluster credit: either row in a multi-row cluster catches it
# ---------------------------------------------------------------------------


def test_duplicate_cluster_caught_by_either_row(tmp_path: Path) -> None:
    """Cluster has 2 rows (original + duplicate). Flagging either should count."""
    labels = [
        _label_row("labevents", "ORIG_A", "inconsistency", "DUP|labevents|A",
                   "in_table_conflict_anchor"),
        _label_row("labevents", "DUP_A", "inconsistency", "DUP|labevents|A",
                   "in_table_conflict"),
        _label_row("labevents", "ORIG_B", "inconsistency", "DUP|labevents|B",
                   "in_table_conflict_anchor"),
        _label_row("labevents", "DUP_B", "inconsistency", "DUP|labevents|B",
                   "in_table_conflict"),
    ]
    _write_labels(tmp_path / "labels.csv", labels)

    # Submission flags only the originals.
    _write_submission(
        tmp_path / "submission" / "flagged_rows.csv",
        [
            {"table": "labevents", "_row_id": "ORIG_A"},
            {"table": "labevents", "_row_id": "ORIG_B"},
        ],
    )
    f1 = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["recall"] == pytest.approx(1.0), "flagging only originals should still catch both clusters"
    assert metrics["precision"] == pytest.approx(1.0), "originals are in labeled rows so precision is 1.0"
    assert f1 == pytest.approx(1.0)
    assert metrics["n_clusters"] == 2
    assert metrics["n_clusters_caught"] == 2


def test_duplicate_cluster_caught_by_only_duplicates(tmp_path: Path) -> None:
    labels = [
        _label_row("labevents", "ORIG_A", "inconsistency", "DUP|labevents|A",
                   "in_table_conflict_anchor"),
        _label_row("labevents", "DUP_A", "inconsistency", "DUP|labevents|A",
                   "in_table_conflict"),
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    _write_submission(
        tmp_path / "submission" / "flagged_rows.csv",
        [{"table": "labevents", "_row_id": "DUP_A"}],
    )
    evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["recall"] == pytest.approx(1.0)


def test_partial_cluster_recall(tmp_path: Path) -> None:
    """3 clusters total, 1 caught -> recall = 1/3, precision = 1.0, F1 = 0.5,
    reward = 0 (binary pass criterion requires recall == 1.0)."""
    labels = [
        _label_row("labevents", f"r{i}", "impossible_value", f"labevents|r{i}")
        for i in range(3)
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    _write_submission(
        tmp_path / "submission" / "flagged_rows.csv",
        [{"table": "labevents", "_row_id": "r0"}],
    )
    reward = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["recall"] == pytest.approx(1 / 3)
    assert metrics["precision"] == pytest.approx(1.0)
    assert metrics["f1"] == pytest.approx(0.5)
    # Binary pass: recall < 1.0, so fail.
    assert reward == 0.0
    assert metrics["n_pass"] == 0


# ---------------------------------------------------------------------------
# Per-family / per-subtype breakdown
# ---------------------------------------------------------------------------


def test_per_family_breakdown(tmp_path: Path) -> None:
    labels = [
        _label_row("labevents", "r0", "impossible_value", "labevents|r0"),
        _label_row("labevents", "r1", "impossible_value", "labevents|r1"),
        _label_row("chartevents", "f0", "fk_violation", "chartevents|f0"),
        _label_row("chartevents", "f1", "fk_violation", "chartevents|f1"),
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    # Flag only the impossible_value rows.
    _write_submission(
        tmp_path / "submission" / "flagged_rows.csv",
        [
            {"table": "labevents", "_row_id": "r0"},
            {"table": "labevents", "_row_id": "r1"},
        ],
    )
    evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["per_family_recall"]["impossible_value"] == pytest.approx(1.0)
    assert metrics["per_family_recall"]["fk_violation"] == pytest.approx(0.0)
    assert metrics["recall"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------


def test_missing_submission_yields_zero(tmp_path: Path) -> None:
    labels = [
        _label_row("labevents", "r0", "impossible_value", "labevents|r0"),
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    f1 = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    assert f1 == 0.0
    assert (tmp_path / "logs" / "verifier_error.txt").exists()


def test_flooding_low_precision_fails_pass_criterion(tmp_path: Path) -> None:
    """Flooding noise rows tanks precision even at recall=1.
    Pass criterion (precision > 0.5) fails -> reward = 0."""
    labels = [
        _label_row("labevents", f"r{i}", "impossible_value", f"labevents|r{i}")
        for i in range(5)
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    sub = [{"table": L["table"], "_row_id": L["row_id"]} for L in labels]
    sub.extend({"table": "labevents", "_row_id": f"NOISE{i}"} for i in range(95))
    _write_submission(tmp_path / "submission" / "flagged_rows.csv", sub)
    reward = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["precision"] == pytest.approx(5 / 100)
    # F1 stays as a diagnostic.
    assert metrics["f1"] == pytest.approx(2 * 0.05 * 1.0 / (0.05 + 1.0))
    # Binary pass: precision < 0.5, so fail.
    assert reward == 0.0
    assert metrics["n_pass"] == 0


def test_pass_criterion_recall1_precision_above_half(tmp_path: Path) -> None:
    """recall == 1.0 AND precision > 0.5 -> reward = 1.0."""
    labels = [
        _label_row("labevents", f"r{i}", "impossible_value", f"labevents|r{i}")
        for i in range(4)
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    # All 4 true positives + 2 noise -> precision = 4/6 ≈ 0.667 > 0.5
    sub = [{"table": L["table"], "_row_id": L["row_id"]} for L in labels]
    sub.extend({"table": "labevents", "_row_id": f"NOISE{i}"} for i in range(2))
    _write_submission(tmp_path / "submission" / "flagged_rows.csv", sub)
    reward = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["precision"] == pytest.approx(4 / 6)
    assert reward == 1.0
    assert metrics["n_pass"] == 1


def test_pass_criterion_precision_exactly_half_fails(tmp_path: Path) -> None:
    """precision == 0.5 (boundary) is NOT a pass — threshold is strict >."""
    labels = [
        _label_row("labevents", f"r{i}", "impossible_value", f"labevents|r{i}")
        for i in range(3)
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    # All 3 TP + 3 noise -> precision = 3/6 = 0.5 exactly
    sub = [{"table": L["table"], "_row_id": L["row_id"]} for L in labels]
    sub.extend({"table": "labevents", "_row_id": f"NOISE{i}"} for i in range(3))
    _write_submission(tmp_path / "submission" / "flagged_rows.csv", sub)
    reward = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["precision"] == pytest.approx(0.5)
    assert reward == 0.0  # strict > 0.5


def test_selective_high_f1(tmp_path: Path) -> None:
    """Submitting exactly the 5 correct rows yields F1 = 1.0 AND reward = 1.0."""
    labels = [
        _label_row("labevents", f"r{i}", "impossible_value", f"labevents|r{i}")
        for i in range(5)
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    sub = [{"table": L["table"], "_row_id": L["row_id"]} for L in labels]
    _write_submission(tmp_path / "submission" / "flagged_rows.csv", sub)
    reward = evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["f1"] == pytest.approx(1.0)
    assert reward == 1.0


def test_turn_count_recorded_when_present(tmp_path: Path) -> None:
    labels = [_label_row("labevents", "r0", "impossible_value", "labevents|r0")]
    _write_labels(tmp_path / "labels.csv", labels)
    _write_submission(tmp_path / "submission" / "flagged_rows.csv", [])
    evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
        turn_count_override=42,
    )
    metrics = json.loads((tmp_path / "logs" / "metrics.json").read_text())
    assert metrics["turn_count"] == 42


def test_handles_alternate_column_names(tmp_path: Path) -> None:
    labels = [_label_row("labevents", "r0", "impossible_value", "labevents|r0")]
    _write_labels(tmp_path / "labels.csv", labels)
    path = tmp_path / "submission" / "flagged_rows.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"Table": "labevents", "Row_Id": "r0"}]).to_csv(path, index=False)
    f1 = evaluate(path, tmp_path / "labels.csv", tmp_path / "logs")
    assert f1 == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Output file shape — Harbor verifier reads reward.json (NOT reward.txt)
# ---------------------------------------------------------------------------


def test_writes_flat_reward_json_only(tmp_path: Path) -> None:
    """reward.txt should NOT be written (Harbor reads it first and would
    mask reward.json's pooled per-trial payload). reward.json must be a
    flat ``dict[str, float|int]`` so Harbor's pydantic schema accepts it.
    """
    labels = [
        _label_row("labevents", "r0", "impossible_value", "labevents|r0"),
        _label_row("prescriptions", "rx0", "demographic_conflict", "DEMO|x|rx0"),
    ]
    _write_labels(tmp_path / "labels.csv", labels)
    _write_submission(
        tmp_path / "submission" / "flagged_rows.csv",
        [{"table": "labevents", "_row_id": "r0"}],
    )
    evaluate(
        tmp_path / "submission" / "flagged_rows.csv",
        tmp_path / "labels.csv",
        tmp_path / "logs",
    )
    log_dir = tmp_path / "logs"
    # reward.txt must not exist.
    assert not (log_dir / "reward.txt").exists()
    # reward.json: flat scalars only, with promoted fam_/sub_ keys.
    payload = json.loads((log_dir / "reward.json").read_text())
    for k, v in payload.items():
        assert isinstance(k, str), f"key {k!r} is not a string"
        assert isinstance(v, (int, float)), (
            f"reward.json[{k}] = {v!r} is not float|int (Harbor pydantic schema)"
        )
    # Canonical Harbor scalars (xray_report_gen convention).
    assert "reward" in payload
    assert "n_tasks" in payload
    assert "n_pass" in payload
    assert "pass_rate" in payload
    assert payload["reward"] in (0.0, 1.0)  # binary
    assert payload["reward"] == payload["pass_rate"]
    # F1 still reported alongside reward for paper-baselines rendering.
    assert "f1" in payload
    # Per-family breakdowns flattened with fam_ / sub_ prefixes.
    assert "fam_impossible_value" in payload
    assert "fam_demographic_conflict" in payload
    assert payload["fam_impossible_value"] == pytest.approx(1.0)
    assert payload["fam_demographic_conflict"] == pytest.approx(0.0)
    # turn_count is encoded as -1 sentinel when missing.
    assert payload["turn_count"] == -1
