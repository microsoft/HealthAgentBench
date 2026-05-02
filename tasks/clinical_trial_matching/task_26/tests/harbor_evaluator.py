"""NDCG-based verifier for the clinical_trial_matching benchmark.

Each task scores one patient topic. The agent's submission at
``/workspace/submission/run.txt`` follows the standard TREC ad-hoc
retrieval format::

    TOPIC_NO Q0 NCT_ID RANK SCORE RUN_NAME

The verifier loads the per-topic ``qrels.txt`` (graded judgments
``{topic_id: {nct_id: int}}`` with grades 0=non-relevant, 1=excluded,
2=eligible) and computes NDCG@10 (the reward), NDCG@1000, and
recall@1000 via pytrec_eval. NDCG@10 is the headline metric.

Output files written to ``log_dir`` (Harbor's verifier log dir):

- ``metrics.json`` — full diagnostic payload (nested dicts allowed).
- ``reward.json`` — flat ``dict[str, float|int]`` Harbor reads (Harbor's
  reward.json schema is ``dict[str, float | int]``; nested dicts must be
  flattened).
- ``reward.txt`` is **not** written. Harbor reads ``reward.txt`` first
  when present, which masks the rich payload and prevents the
  uv-script aggregator from receiving per-trial diagnostics.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytrec_eval


REQUIRED_RUN_FIELDS = 6


def _read_turn_count() -> int | None:
    candidates = [
        Path("/logs/agent_turn_count.txt"),
        Path("/workspace/.harbor/agent_turn_count.txt"),
    ]
    for p in candidates:
        if p.exists():
            try:
                return int(p.read_text().strip())
            except (OSError, ValueError):
                continue
    return None


def _load_qrels(path: Path) -> dict[str, dict[str, int]]:
    """Parse a TREC qrels file: ``topic_no 0 doc_id grade`` per line."""
    qrels: dict[str, dict[str, int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        topic, _, doc, grade = parts
        try:
            qrels.setdefault(topic, {})[doc] = int(grade)
        except ValueError:
            continue
    return qrels


def _load_run(path: Path) -> tuple[dict[str, dict[str, float]], int]:
    """Parse a TREC run file. Returns (run_dict, n_rows). Tolerates blank
    lines, comments, and duplicate (topic, doc) — keeps the highest score.
    Returns an empty run on parse failure.
    """
    run: dict[str, dict[str, float]] = {}
    n_rows = 0
    if not path.exists():
        return run, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != REQUIRED_RUN_FIELDS:
            # Be lenient — some agents drop the Q0 column. Reject only on
            # gross-format errors (< 4 fields).
            if len(parts) < 4:
                continue
        # Fields: TOPIC_NO Q0 NCT_ID RANK SCORE RUN_NAME
        topic = parts[0]
        doc = parts[2] if len(parts) >= 3 else None
        try:
            score = float(parts[4]) if len(parts) >= 5 else float(len(run.get(topic, {})) * -1)
        except ValueError:
            continue
        if doc is None:
            continue
        n_rows += 1
        topic_run = run.setdefault(topic, {})
        # Keep highest score on duplicate (topic, doc).
        prev = topic_run.get(doc)
        if prev is None or score > prev:
            topic_run[doc] = score
    return run, n_rows


def evaluate(
    submission_path: Path,
    qrels_path: Path,
    log_dir: Path,
    turn_count_override: int | None = None,
) -> float:
    """Score a TREC run against the per-topic qrels using NDCG@10.

    Returns the NDCG@10 of the (single) topic in qrels. Writes
    ``metrics.json`` and ``reward.json`` to ``log_dir``. Never raises on
    bad agent input — writes ``verifier_error.txt`` and returns 0.0.
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    qrels = _load_qrels(qrels_path)
    if not qrels:
        (log_dir / "verifier_error.txt").write_text(
            f"qrels file is empty or unparseable: {qrels_path}\n"
        )
        return 0.0

    if len(qrels) != 1:
        # Each task is single-topic by construction. Still continue (the
        # metric is well-defined for multi-topic), but log a warning.
        (log_dir / "verifier_warning.txt").write_text(
            f"qrels has {len(qrels)} topics (expected 1)\n"
        )

    run, n_submission_rows = _load_run(submission_path)

    if not run:
        (log_dir / "verifier_error.txt").write_text(
            f"submission file at {submission_path} missing or unparseable\n"
        )
        # Still emit a zero-reward payload so the aggregator sees this trial.
        _emit(log_dir, qrels, {}, n_submission_rows, turn_count_override)
        return 0.0

    return _emit(log_dir, qrels, run, n_submission_rows, turn_count_override)


def _emit(
    log_dir: Path,
    qrels: dict[str, dict[str, int]],
    run: dict[str, dict[str, float]],
    n_submission_rows: int,
    turn_count_override: int | None,
) -> float:
    """Run pytrec_eval and write metrics.json + reward.json. Returns NDCG@10."""
    measures = {"ndcg_cut.10", "ndcg_cut.1000", "recall.1000"}
    evaluator = pytrec_eval.RelevanceEvaluator(qrels, measures)
    per_topic_scores = evaluator.evaluate(run) if run else {}

    # Single-topic per task; pull the topic's score (or 0 if missing).
    topic_id = next(iter(qrels))
    scores = per_topic_scores.get(topic_id, {})
    ndcg10 = float(scores.get("ndcg_cut_10", 0.0))
    ndcg1000 = float(scores.get("ndcg_cut_1000", 0.0))
    recall1000 = float(scores.get("recall_1000", 0.0))

    # Diagnostic counts.
    judged = qrels.get(topic_id, {})
    n_eligible = sum(1 for g in judged.values() if g == 2)
    n_excluded = sum(1 for g in judged.values() if g == 1)
    n_nonrel = sum(1 for g in judged.values() if g == 0)

    if turn_count_override is not None:
        turn_count: int | None = turn_count_override
    else:
        turn_count = _read_turn_count()

    metrics: dict[str, Any] = {
        "topic_id": topic_id,
        "ndcg_cut_10": ndcg10,
        "ndcg_cut_1000": ndcg1000,
        "recall_1000": recall1000,
        "n_judged_eligible": n_eligible,
        "n_judged_excluded": n_excluded,
        "n_judged_nonrelevant": n_nonrel,
        "n_submission_rows": int(n_submission_rows),
        "n_run_unique_docs": int(len(run.get(topic_id, {}))),
        "turn_count": turn_count,
    }
    (log_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # Flat reward.json (Harbor's pydantic schema is ``dict[str, float|int]``).
    reward_payload: dict[str, float | int] = {
        "reward": ndcg10,
        "ndcg_cut_10": ndcg10,
        "ndcg_cut_1000": ndcg1000,
        "recall_1000": recall1000,
        "n_judged_eligible": n_eligible,
        "n_judged_excluded": n_excluded,
        "n_judged_nonrelevant": n_nonrel,
        "n_submission_rows": int(n_submission_rows),
        "n_run_unique_docs": int(len(run.get(topic_id, {}))),
        # -1 sentinel means "not recorded". Harbor's pydantic schema rejects None.
        "turn_count": int(turn_count) if turn_count is not None else -1,
        "topic_id": int(topic_id) if topic_id.isdigit() else -1,
    }
    (log_dir / "reward.json").write_text(json.dumps(reward_payload, indent=2))
    return ndcg10


def main() -> None:
    submission = Path("/workspace/submission/run.txt")
    qrels = Path(os.environ.get("TREC_CT_QRELS", "/tests/qrels.txt"))
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, qrels, log_dir)
    print(f"ndcg_cut_10={score:.6f}")


if __name__ == "__main__":
    main()
