#!/usr/bin/env python3
"""Harbor verifier for MIMIC-CXR report generation task.

Called by Harbor after the agent completes. Reads submission.json,
compares against task_answer_key.json using BLEU and ROUGE-L,
and outputs verification results.

Expected environment:
    - /workspace/submission.json — agent's generated report
    - /tests/task_answer_key.json — ground-truth report
    - /tests/evaluator.py — evaluation logic
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Import evaluator from local tests directory
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from evaluator import evaluate_submission_rows


def main() -> int:
    workspace_dir = Path("/workspace")
    tests_dir = Path("/tests")
    logs_dir = Path("/logs/verifier")
    logs_dir.mkdir(parents=True, exist_ok=True)

    submission_path = workspace_dir / "submission.json"
    answer_key_path = tests_dir / "task_answer_key.json"

    # Check required files exist
    for path, label in [(submission_path, "Submission"), (answer_key_path, "Answer key")]:
        if not path.exists():
            result = {"reward": 0.0, "status": "error", "error": f"{label} not found: {path}"}
            (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
            (logs_dir / "reward.json").write_text(json.dumps({"total": 0, "filled": 0, "avg_bleu": 0.0, "avg_rouge_l": 0.0, "fill_rate": 0.0, "tasks": []}))
            return 1

    submission_raw = submission_path.read_text()
    try:
        submission = json.loads(submission_raw)
    except json.JSONDecodeError as e:
        # Fallback: try to salvage final_answer fields via regex so a minor
        # formatting error in submission.json does not zero the reward.
        import re

        parse_warning = f"submission.json parse error: {e}; used regex salvage"
        salvaged = []
        # Match "task_id": "...", then find final_answer string value within
        # the same object literal.
        for m in re.finditer(r'"task_id"\s*:\s*"([^"]+)"', submission_raw):
            tid = m.group(1)
            # Search forward from this task_id for a final_answer string.
            tail = submission_raw[m.end():]
            next_tid = re.search(r'"task_id"\s*:', tail)
            obj_end = next_tid.start() if next_tid else len(tail)
            segment = tail[:obj_end]
            fa = re.search(
                r'"final_answer"\s*:\s*"((?:[^"\\]|\\.)*)"', segment, flags=re.DOTALL
            )
            if fa:
                # Decode JSON-escaped string (handles \n, \", \\ etc.)
                try:
                    value = json.loads(f'"{fa.group(1)}"')
                except Exception:
                    value = fa.group(1)
            else:
                value = ""
            salvaged.append({"task_id": tid, "final_answer": value, "payload": None})

        if not salvaged:
            result = {"reward": 0.0, "status": "error", "error": parse_warning}
            (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
            (logs_dir / "reward.json").write_text(json.dumps({"total": 0, "filled": 0, "avg_bleu": 0.0, "avg_rouge_l": 0.0, "fill_rate": 0.0, "tasks": []}))
            return 1
        submission = salvaged
        (logs_dir / "parse_warning.txt").write_text(parse_warning)

    try:
        answer_key = json.loads(answer_key_path.read_text())
    except json.JSONDecodeError as e:
        result = {"reward": 0.0, "status": "error", "error": f"Failed to parse answer key: {e}"}
        (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
        (logs_dir / "reward.txt").write_text("0.0")
        return 1

    # Save agent submission for inspection
    (logs_dir / "submission.json").write_text(json.dumps(submission, indent=2))

    try:
        eval_result = evaluate_submission_rows(submission, answer_key)
    except Exception as e:
        result = {"reward": 0.0, "status": "error", "error": f"Evaluation failed: {e}"}
        (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))
        (logs_dir / "reward.txt").write_text("0.0")
        return 1

    # Use ROUGE-L as the primary reward signal
    reward = eval_result["avg_rouge_l"]

    # Harbor's progress UI formats the first metric value as a float, so the
    # first key must be numeric (not the "status" string).
    result = {
        "reward": reward,
        "status": "success",
        "total_tasks": eval_result["total_tasks"],
        "filled_tasks": eval_result["filled_tasks"],
        "metrics": {
            "avg_bleu": eval_result["avg_bleu"],
            "avg_rouge_l": eval_result["avg_rouge_l"],
            "fill_rate": eval_result["fill_rate"],
        },
        "summary": {
            "total": eval_result["total_tasks"],
            "filled": eval_result["filled_tasks"],
            "avg_bleu": f"{eval_result['avg_bleu']:.4f}",
            "avg_rouge_l": f"{eval_result['avg_rouge_l']:.4f}",
        },
    }

    (logs_dir / "meta_results.json").write_text(json.dumps(result, indent=2))

    # Per-trial CheXbert labels. Aggregator pools these scalars and runs
    # sklearn classification_report — mathematically equivalent to running
    # f1chexbert over the pooled text (verified in scripts/mimic_report_gen/
    # test_aggregation.py). Each reward.json contributes 28 scalar fields:
    # chx_ref_<label> and chx_pred_<label>, one per CheXpert pathology.
    chx_fields: dict[str, int] = {}
    key_by_id = {k["task_id"]: k for k in answer_key}
    chx_error: str | None = None
    if submission:
        # For this benchmark there's always exactly one task per trial. Label
        # that single (prediction, reference) pair and flatten into scalars.
        row = submission[0]
        key = key_by_id.get(row.get("task_id", ""), {})
        pred_text = row.get("final_answer", "") or ""
        ref_text = key.get("expected_answer", "") or ""
        try:
            from chexbert_labeler import (
                label_text,
                label_to_fields,
            )

            ref_vec = label_text(ref_text)
            pred_vec = label_text(pred_text)
            chx_fields.update(label_to_fields("ref", ref_vec))
            chx_fields.update(label_to_fields("pred", pred_vec))
        except Exception as e:
            # Labelling is best-effort — if CheXbert can't load (missing
            # weights, no internet on first run, etc.) we still emit the
            # scalar metrics and record the error inside meta_results.json.
            chx_error = f"{type(e).__name__}: {e}"
            (logs_dir / "chexbert_error.txt").write_text(chx_error)

    # reward.json — scalar-only (Harbor validates `rewards: dict[str, float|int]`).
    reward_payload: dict[str, float | int] = {
        "reward": reward,
        "total": eval_result["total_tasks"],
        "filled": eval_result["filled_tasks"],
        "avg_bleu": eval_result["avg_bleu"],
        "avg_rouge_l": eval_result["avg_rouge_l"],
        "fill_rate": eval_result["fill_rate"],
    }
    reward_payload.update(chx_fields)
    (logs_dir / "reward.json").write_text(json.dumps(reward_payload))

    # tasks.jsonl — per-task raw text (kept for debugging / re-scoring with
    # different metrics). Not required by the aggregator now that labels
    # travel in reward.json.
    with (logs_dir / "tasks.jsonl").open("w") as f:
        for row in submission:
            tid = row.get("task_id", "")
            key = key_by_id.get(tid, {})
            json.dump(
                {
                    "task_id": tid,
                    "prediction": row.get("final_answer", ""),
                    "reference": key.get("expected_answer", ""),
                    "expected_findings": key.get("expected_findings", ""),
                    "expected_impression": key.get("expected_impression", ""),
                },
                f,
            )
            f.write("\n")

    # Detailed per-task results
    (logs_dir / "detailed_results.json").write_text(
        json.dumps(
            {
                "summary": result["summary"],
                "tasks": eval_result["results"],
            },
            indent=2,
        )
    )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
