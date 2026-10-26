#!/usr/bin/env python3
"""Strict task-level exact match: every ACL and meniscus answer for every exam must be correct."""

import argparse
import json
from pathlib import Path

ANSWER_KEYS = ("acl", "meniscus")


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def is_binary(value):
    return type(value) is int and value in (0, 1)


def score(payload, expected):
    slots = sorted(expected)
    total = len(slots) * len(ANSWER_KEYS)
    base = {"reward": 0.0, "correct_answers": 0, "total_questions": total}
    if not isinstance(payload, dict) or set(payload) != set(slots):
        return {**base, "error": f"Expected exactly the keys {slots}."}
    for slot in slots:
        answer = payload[slot]
        if not isinstance(answer, dict) or set(answer) != set(ANSWER_KEYS):
            return {**base, "error": f"{slot} must have exactly the keys {list(ANSWER_KEYS)}."}
        if not all(is_binary(answer[k]) for k in ANSWER_KEYS):
            return {**base, "error": f"{slot} answers must be integers 0 or 1."}
    per_exam = {
        slot: sum(payload[slot][k] == expected[slot][k] for k in ANSWER_KEYS) for slot in slots
    }
    correct = sum(per_exam.values())
    return {
        "reward": float(correct == total),
        "correct_answers": correct,
        "total_questions": total,
        "per_exam_correct": per_exam,
        "error": None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, default=Path("/workspace/submission.json"))
    parser.add_argument("--gold", type=Path, default=Path("/tests/gold.json"))
    parser.add_argument("--output", type=Path, default=Path("/logs/verifier"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    # Fail closed even if infrastructure/answer-key loading fails.
    (args.output / "reward.txt").write_text("0.0\n")
    expected = json.loads(args.gold.read_text())["answers"]
    if not expected or any(
        set(v) != set(ANSWER_KEYS) or not all(is_binary(x) for x in v.values())
        for v in expected.values()
    ):
        raise ValueError("Invalid verifier answer key")
    try:
        if args.submission.stat().st_size > 65536:
            raise ValueError("Submission is too large")
        payload = json.loads(args.submission.read_text(), object_pairs_hook=unique_object)
        metrics = score(payload, expected)
        metrics["submission"] = payload  # recorded for post-hoc error analysis
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        metrics = {"reward": 0.0, "correct_answers": 0, "error": str(exc)}
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (args.output / "reward.txt").write_text(f"{metrics['reward']:.1f}\n")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
