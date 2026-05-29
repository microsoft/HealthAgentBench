"""Smoke tests for scripts/ehr_data_quality/aggregate_metric.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
AGG = REPO_ROOT / "scripts" / "ehr_data_quality" / "aggregate_metric.py"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def _run(input_path: Path, output_path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(AGG), "-i", str(input_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert output_path.exists(), result.stderr
    return json.loads(output_path.read_text())


def test_pools_metrics_across_trials(tmp_path: Path) -> None:
    rewards = [
        {
            "f1": 0.8, "recall": 1.0, "precision": 2 / 3,
            "n_clusters": 10, "n_clusters_caught": 10,
            "n_flagged_rows": 15, "n_useful_flagged_rows": 10,
            "per_family_recall": {"impossible_value": 1.0},
            "per_subtype_recall": {"range_extreme": 1.0},
            "turn_count": 12,
        },
        {
            "f1": 0.5, "recall": 0.5, "precision": 0.5,
            "n_clusters": 20, "n_clusters_caught": 10,
            "n_flagged_rows": 20, "n_useful_flagged_rows": 10,
            "per_family_recall": {"temporal_violation": 0.5},
            "per_subtype_recall": {"med_after_discharge": 0.5},
            "turn_count": 18,
        },
    ]
    _write_jsonl(tmp_path / "rewards.jsonl", rewards)
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")

    # Macro means
    assert out["mean_f1"] == 0.65
    assert out["mean_recall"] == 0.75
    # Micro: caught=20 of 30 clusters; useful=20 of 35 flagged rows
    assert out["micro_recall"] == round(20 / 30, 4)
    assert out["micro_precision"] == round(20 / 35, 4)
    assert out["n_trials"] == 2
    assert out["n_clusters_total"] == 30
    assert out["n_clusters_caught_total"] == 20
    assert out["mean_turn_count"] == 15.0
    assert "impossible_value" in out["per_family_recall_macro"]
    assert "temporal_violation" in out["per_family_recall_macro"]


def test_handles_bare_scalar_lines(tmp_path: Path) -> None:
    """Falls back gracefully when reward.jsonl just contains numeric scalars.
    Bare scalars carry no F1, so diagnostic metrics default to 0; headline
    `reward` is the simple mean of the scalars (mirrors xray_report_gen)."""
    (tmp_path / "rewards.jsonl").write_text("0.5\n0.7\n")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out["n_trials"] == 2
    assert abs(out["reward"] - 0.6) < 1e-6
    # No bare scalar >= 1.0 -> zero successes (binary pass).
    assert out["success"] == 0
    assert out["mean_f1"] == 0.0  # bare scalars carry no F1 diagnostic


def test_empty_input(tmp_path: Path) -> None:
    (tmp_path / "rewards.jsonl").write_text("")
    out = _run(tmp_path / "rewards.jsonl", tmp_path / "metric.json")
    assert out == {"error": "no rewards"}


def test_prefers_run_dir_reward_jsons_over_jsonl(tmp_path: Path) -> None:
    """When the input path is rewards.jsonl inside a Harbor run dir, the
    aggregator scans <run_dir>/<task_*>/verifier/reward.json for richer
    per-trial metrics rather than the bare scalar in rewards.jsonl.
    """
    run_dir = tmp_path / "run_2026"
    run_dir.mkdir()
    # Two trials with rich reward.json files (harbor would only put scalars
    # in rewards.jsonl, but the verifier wrote the full payload).
    for i, f1_value in enumerate([0.8, 0.5]):
        td = run_dir / f"task_X_{i}__abc{i}"
        (td / "verifier").mkdir(parents=True)
        (td / "verifier" / "reward.json").write_text(
            json.dumps(
                {
                    "reward": f1_value,
                    "f1": f1_value,
                    "recall": 1.0 if i == 0 else 0.5,
                    "precision": 2 / 3 if i == 0 else 0.5,
                    "n_clusters": 10,
                    "n_clusters_caught": 10 if i == 0 else 5,
                    "n_flagged_rows": 15 if i == 0 else 10,
                    "n_useful_flagged_rows": 10 if i == 0 else 5,
                    "per_family_recall": {"impossible_value": 1.0 if i == 0 else 0.5},
                    "per_subtype_recall": {"range_extreme": 1.0 if i == 0 else 0.5},
                    "turn_count": 10 + i,
                }
            )
        )
    # Bare scalar rewards.jsonl (what Harbor would write) — should be ignored.
    (run_dir / "rewards.jsonl").write_text("0.0\n0.0\n")
    out = _run(run_dir / "rewards.jsonl", tmp_path / "metric.json")
    # Mean F1 should reflect rich reward.json values (0.8 + 0.5)/2 = 0.65,
    # not the 0.0 scalars from rewards.jsonl.
    assert out["mean_f1"] == 0.65
    assert out["mean_recall"] == 0.75
    assert out["mean_precision"] == round((2 / 3 + 0.5) / 2, 4)
    assert out["per_family_recall_macro"]["impossible_value"] == 0.75
    assert out["n_clusters_total"] == 20
