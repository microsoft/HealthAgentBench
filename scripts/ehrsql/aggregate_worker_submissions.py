#!/usr/bin/env python3
"""Aggregate all worker submissions and run evaluation on the combined set.

This script:
1. Finds all worker submission.json files from a Harbor run
2. Merges them preserving original task_id order
3. Runs evaluation using harbor_evaluator.py on the combined submission
4. Generates a comprehensive evaluation report
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_latest_run(results_dir: Path) -> Path:
    """Find the latest Harbor run directory."""
    run_dirs = sorted(results_dir.glob("*/"), reverse=True)
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {results_dir}")
    return run_dirs[0]


def find_worker_submissions(run_dir: Path) -> list[tuple[int, Path]]:
    """Find all worker submission.json files, returning (worker_id, path) tuples."""
    submissions = []
    for worker_dir in sorted(run_dir.glob("worker_*__*")):
        worker_num_str = worker_dir.name.split("__")[0].replace("worker_", "")
        try:
            worker_num = int(worker_num_str)
        except ValueError:
            continue

        submission_path = worker_dir / "artifacts" / "submission.json"
        if submission_path.exists():
            submissions.append((worker_num, submission_path))

    return sorted(submissions, key=lambda x: x[0])


def find_answer_key(run_dirs: list[Path], output_dir: Path) -> Path:
    """Merge answer keys by resolving task paths from each worker's config.json.

    Each worker's config.json contains a task.path that points to the
    original task directory. We use that to find the per-worker answer key.
    """
    all_answers: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    key_count = 0

    for rd in run_dirs:
        for worker_dir in sorted(rd.glob("worker_*__*")):
            config_path = worker_dir / "config.json"
            if not config_path.exists():
                continue

            task_path = Path(json.loads(config_path.read_text())["task"]["path"])
            ak_path = task_path / "tests" / "task_answer_key.json"
            if not ak_path.exists():
                continue

            key_count += 1
            for row in json.loads(ak_path.read_text()):
                if row["task_id"] not in seen_ids:
                    all_answers.append(row)
                    seen_ids.add(row["task_id"])

    if not all_answers:
        raise FileNotFoundError(f"Could not find any answer keys from run dirs: {run_dirs}")

    merged_path = output_dir / "merged_answer_key.json"
    merged_path.write_text(json.dumps(all_answers, indent=2))
    print(f"✓ Merged {len(all_answers)} answer keys from {key_count} workers -> {merged_path}")
    return merged_path



def merge_submissions(
    submissions: list[tuple[int, Path]],
    task_id_order: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Merge all worker submissions into a single list, preserving original task order."""
    print(f"📦 Merging {len(submissions)} worker submissions...")
    all_rows = []
    total_filled = 0
    total_empty = 0
    workers_with_gaps: list[tuple[int, int, int]] = []  # (worker_num, empty, total)

    for worker_num, submission_path in submissions:
        try:
            rows = json.loads(submission_path.read_text())
            filled = sum(1 for r in rows if r.get("final_answer", "").strip())
            empty = len(rows) - filled
            total_filled += filled
            total_empty += empty
            status = "✓" if empty == 0 else "⚠️"
            print(f"   {status} worker_{worker_num}: {filled}/{len(rows)} filled")
            if empty > 0:
                workers_with_gaps.append((worker_num, empty, len(rows)))
            all_rows.extend(rows)
        except Exception as e:
            print(f"   ✗ worker_{worker_num}: {e}")
            continue

    # Report completeness
    total = total_filled + total_empty
    if total_empty > 0:
        print(f"\n⚠️  {total_empty}/{total} tasks have empty final_answer:")
        for wnum, empty, wtotal in workers_with_gaps:
            print(f"   worker_{wnum}: {empty}/{wtotal} empty")
    else:
        print(f"\n✓ All {total} tasks have final_answer filled")

    # Sort by original task_id order if available
    if task_id_order:
        all_rows.sort(key=lambda r: task_id_order.get(r.get("task_id"), 999999))

    return all_rows


def run_evaluation(
    submission_path: Path,
    answer_key_path: Path,
    db_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run the harbor_evaluator on the merged submission."""
    print(f"\n🔍 Running evaluation...")
    print(f"   Submission: {submission_path}")
    print(f"   Answer key: {answer_key_path}")
    print(f"   Databases: {db_dir}")

    cmd = [
        "uv",
        "run",
        "python",
        "scripts/ehrsql/harbor_evaluator.py",
        "--submission",
        str(submission_path),
        "--answer-key",
        str(answer_key_path),
        "--db-dir",
        str(db_dir),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent.parent,  # Project root
            timeout=3600,  # 1 hour timeout
        )

        if result.returncode != 0:
            print(f"   ✗ Evaluation failed: {result.stderr}")
            return {}

        evaluation_result = json.loads(result.stdout)
        return evaluation_result

    except subprocess.TimeoutExpired:
        print("   ✗ Evaluation timed out (1 hour)")
        return {}
    except Exception as e:
        print(f"   ✗ Evaluation error: {e}")
        return {}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Aggregate worker submissions and run evaluation"
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        nargs="+",
        help="One or more Harbor run directories (auto-detected if not specified)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results/harbor/ehrsql/mimic_iii_valid"),
        help="Base results directory",
    )
    parser.add_argument(
        "--db-dir",
        type=Path,
        default=Path("/data/ehrsql"),
        help="Database directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for aggregated results (default: run_dir)",
    )
    args = parser.parse_args()

    # Find run directories
    if args.run_dir:
        run_dirs = args.run_dir
    else:
        results_dir = args.results_dir.resolve()
        run_dirs = [find_latest_run(results_dir)]

    for rd in run_dirs:
        print(f"📂 Run directory: {rd}")
    output_dir = args.output_dir or run_dirs[0]

    # Find worker submissions across all run directories
    submissions = []
    seen_workers: set[int] = set()
    for rd in run_dirs:
        for worker_num, path in find_worker_submissions(rd):
            if worker_num not in seen_workers:
                submissions.append((worker_num, path))
                seen_workers.add(worker_num)
    submissions.sort(key=lambda x: x[0])

    if not submissions:
        print("✗ No worker submissions found")
        return 1

    print(f"✓ Found {len(submissions)} worker submissions")
    for worker_num, path in submissions:
        print(f"   worker_{worker_num}: {path}")

    # Load task order (not critical, just for ordering)
    task_id_order: dict[str, int] = {}

    # Merge submissions
    merged_submission = merge_submissions(submissions, task_id_order)
    print(f"✓ Merged into {len(merged_submission)} total tasks")

    # Write merged submission
    merged_submission_path = output_dir / "merged_submission.json"
    merged_submission_path.write_text(json.dumps(merged_submission, indent=2))
    print(f"✓ Wrote merged submission: {merged_submission_path}")

    # Find answer key
    try:
        answer_key_path = find_answer_key(run_dirs, output_dir)
        print(f"✓ Found answer key: {answer_key_path}")
    except FileNotFoundError as e:
        print(f"✗ {e}")
        return 1

    # Run evaluation
    evaluation_result = run_evaluation(
        merged_submission_path,
        answer_key_path,
        args.db_dir,
        output_dir,
    )

    if not evaluation_result:
        print("⚠️  Evaluation did not produce results")
        return 1

    # Write evaluation results
    eval_output_path = output_dir / "merged_evaluation.json"
    eval_output_path.write_text(json.dumps(evaluation_result, indent=2))
    print(f"\n✅ Evaluation complete!")
    print(f"   Results: {eval_output_path}")

    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total tasks: {evaluation_result.get('total_tasks', '?')}")
    print(f"   Passed: {evaluation_result.get('passed_tasks', '?')}")
    print(f"   Pass@1: {evaluation_result.get('pass_at_1', '?'):.1%}")
    if "f1_ans" in evaluation_result:
        print(f"   Precision (ans): {evaluation_result.get('precision_ans', '?')}%")
        print(f"   Recall (ans): {evaluation_result.get('recall_ans', '?')}%")
        print(f"   F1 (ans): {evaluation_result.get('f1_ans', '?')}%")
    if "precision_exec" in evaluation_result:
        print(f"   Precision (exec): {evaluation_result.get('precision_exec', '?')}%")
        print(f"   Recall (exec): {evaluation_result.get('recall_exec', '?')}%")
        print(f"   F1 (exec): {evaluation_result.get('f1_exec', '?')}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
