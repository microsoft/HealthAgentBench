"""Score an ehr_compositional_qa submission against the hidden answer key.

Usage:

    python evaluator.py \\
        --submission /workspace/submission.json \\
        --answer-key /tests/answer_key.json \\
        --metrics-out /logs/verifier/metrics.json \\
        --reward-out /logs/verifier/reward.json

Scoring rule (per question, from the answer key's ``tolerance`` field):

    integer     correct  ↔  |answer - gt_answer|  <   0.5
    continuous  correct  ↔  |answer - gt_answer|  <=  max(rel * |gt_answer|, abs)

A ``gt_answer`` of ``"not_applicable"`` (the question cannot be answered for its
patient) is matched only by that exact string; a numeric ``gt_answer`` never is.

Outputs ``metrics.json`` with per-concept breakdown and ``reward.json`` with
``{"reward": 1.0}`` only when every answer is correct, otherwise 0.0.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

NOT_APPLICABLE = "not_applicable"


def is_correct(pred: object, gt: float | str, tolerance: dict) -> bool:
    if gt == NOT_APPLICABLE:
        return pred == NOT_APPLICABLE
    if isinstance(pred, bool) or not isinstance(pred, (int, float)):
        return False
    try:
        pred_f = float(pred)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return False
    if not math.isfinite(pred_f):
        return False
    if tolerance["kind"] == "integer":
        return abs(pred_f - gt) < 0.5
    return abs(pred_f - gt) <= max(tolerance["rel"] * abs(gt), tolerance["abs"])


def valid_tolerance(tol: object) -> bool:
    if not isinstance(tol, dict) or tol.get("kind") not in ("integer", "continuous"):
        return False
    if tol["kind"] == "integer":
        return True
    return all(
        not isinstance(tol.get(f), bool) and isinstance(tol.get(f), (int, float))
        and math.isfinite(tol[f]) and tol[f] >= 0
        for f in ("rel", "abs")
    )


def score_submission(submission_path: Path, answer_key_path: Path) -> dict:
    answer_key = json.loads(answer_key_path.read_text())

    # The question count is defined by the answer key (one task per question type).
    if not isinstance(answer_key, list) or not answer_key:
        raise ValueError(f"answer_key.json at {answer_key_path} must be a non-empty list of questions")
    n_questions = len(answer_key)
    key_ids = [r["question_id"] for r in answer_key]
    if any(not isinstance(qid, str) for qid in key_ids) or len(set(key_ids)) != n_questions:
        raise ValueError("answer_key must contain unique string question IDs")
    for r in answer_key:
        gt = r.get("gt_answer")
        if gt != NOT_APPLICABLE and (
                isinstance(gt, bool) or not isinstance(gt, (int, float)) or not math.isfinite(gt)):
            raise ValueError(f"answer_key has invalid gt_answer for {r.get('question_id')}: {gt!r}")
        if not valid_tolerance(r.get("tolerance")):
            raise ValueError(f"answer_key has invalid tolerance for {r.get('question_id')}: {r.get('tolerance')!r}")

    submission_obj = None
    error: str | None = None
    if not submission_path.exists():
        error = f"submission not found at {submission_path}"
    else:
        try:
            submission_obj = json.loads(submission_path.read_text())
        except json.JSONDecodeError as e:
            error = f"submission.json is not valid JSON: {e}"
        else:
            if not isinstance(submission_obj, list):
                error = "submission.json must be a JSON list"

    sub_by_id: dict[str, object] = {}
    if isinstance(submission_obj, list):
        for r in submission_obj:
            if not isinstance(r, dict) or set(r) != {"question_id", "answer"}:
                error = "each submission row must contain exactly question_id and answer"
                continue
            qid = r["question_id"]
            if not isinstance(qid, str) or qid not in key_ids:
                error = "submission contains an invalid or unknown question_id"
                continue
            if qid in sub_by_id:
                error = f"duplicate question_id: {qid}"
                continue
            sub_by_id[qid] = r["answer"]
        if len(submission_obj) != n_questions or set(sub_by_id) != set(key_ids):
            error = error or f"submission must contain each of the {n_questions} question IDs exactly once"

    per_question: list[dict] = []
    by_concept_correct: dict[str, int] = defaultdict(int)
    by_concept_total: dict[str, int] = defaultdict(int)
    correct = 0
    for r in answer_key:
        qid = r["question_id"]
        concept = r["concept"]
        gt = r["gt_answer"]
        pred = sub_by_id.get(qid)
        ok = is_correct(pred, gt, r["tolerance"])
        per_question.append({
            "question_id": qid,
            "concept": concept,
            "predicted": pred,
            "correct": ok,
        })
        by_concept_total[concept] += 1
        if ok:
            correct += 1
            by_concept_correct[concept] += 1

    total = len(answer_key)
    pass_rate_overall = correct / total if total else 0.0
    pass_rate_by_concept = {
        c: (by_concept_correct[c] / by_concept_total[c]) for c in sorted(by_concept_total)
    }

    metrics: dict = {
        "passed": error is None and correct == total,
        "pass_rate_overall": pass_rate_overall,
        "pass_rate_by_concept": pass_rate_by_concept,
        "total_questions": total,
        "correct": correct,
        "per_question": per_question,
    }
    if error:
        metrics["error"] = error
    return metrics


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--submission", type=Path, required=True)
    p.add_argument("--answer-key", type=Path, required=True)
    p.add_argument("--metrics-out", type=Path, required=True)
    p.add_argument("--reward-out", type=Path, required=True)
    args = p.parse_args()

    metrics = score_submission(args.submission, args.answer_key)
    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    args.reward_out.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_out.write_text(json.dumps(metrics, indent=2) + "\n")
    args.reward_out.write_text(json.dumps({"reward": float(metrics["passed"])}) + "\n")
    print(
        f"[evaluator] pass_rate={metrics['pass_rate_overall']:.4f} "
        f"correct={metrics['correct']}/{metrics['total_questions']}"
        + (f" error={metrics.get('error')}" if metrics.get('error') else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
