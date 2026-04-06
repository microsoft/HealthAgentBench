# /// script
# dependencies = []
# ///
"""Harbor uv-script metric: aggregate per-task EHRSQL rewards into global metrics.

Computes the same precision/recall/F1 (answerability and execution) that
harbor_evaluator.py would produce if all tasks were evaluated together.

Each trial's reward.json contains raw binary counts:
  pred_not_null, real_not_null, both_not_null,
  exec_match_given_pred, exec_match_given_real,
  total, passed

This script sums those counts across trials and derives:
  precision_ans  = both_not_null / pred_not_null
  recall_ans     = both_not_null / real_not_null
  f1_ans         = harmonic mean
  precision_exec = exec_match_given_pred / pred_not_null
  recall_exec    = exec_match_given_real / real_not_null
  f1_exec        = harmonic mean

Usage (called by Harbor automatically via metrics config):
    uv run scripts/ehrsql/aggregate_metric.py -i rewards.jsonl -o metric.json
"""

import argparse
import json
import sys
from pathlib import Path


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r + 1e-10)


def main(input_path: Path, output_path: Path) -> None:
    keys = [
        "pred_not_null", "real_not_null", "both_not_null",
        "exec_match_given_pred", "exec_match_given_real",
        "total", "passed", "filled",
    ]
    sums = {k: 0 for k in keys}
    n_trials = 0

    for line in input_path.read_text().splitlines():
        reward = json.loads(line)
        if reward is None:
            continue
        n_trials += 1
        for k in keys:
            sums[k] += reward.get(k, 0)

    if n_trials == 0:
        output_path.write_text(json.dumps({"error": "no rewards"}))
        return

    pn = sums["pred_not_null"]
    rn = sums["real_not_null"]

    precision_ans = sums["both_not_null"] / (pn + 1e-10)
    recall_ans = sums["both_not_null"] / (rn + 1e-10)
    f1_ans = _f1(precision_ans, recall_ans)

    precision_exec = sums["exec_match_given_pred"] / (pn + 1e-10)
    recall_exec = sums["exec_match_given_real"] / (rn + 1e-10)
    f1_exec = _f1(precision_exec, recall_exec)

    pass_at_1 = sums["passed"] / sums["total"] if sums["total"] else 0.0

    result = {
        "precision_ans": round(100.0 * precision_ans, 2),
        "recall_ans": round(100.0 * recall_ans, 2),
        "f1_ans": round(100.0 * f1_ans, 2),
        "precision_exec": round(100.0 * precision_exec, 2),
        "recall_exec": round(100.0 * recall_exec, 2),
        "f1_exec": round(100.0 * f1_exec, 2),
        "pass_at_1": round(pass_at_1, 4),
        "total_tasks": sums["total"],
        "passed_tasks": sums["passed"],
        "filled_tasks": sums["filled"],
        "fill_rate": round(sums["filled"] / sums["total"], 4) if sums["total"] else 0.0,
        "num_trials": n_trials,
    }

    output_path.write_text(json.dumps(result, indent=2))

    # Print summary to stderr (visible in Harbor output)
    print(f"\n{'='*44}", file=sys.stderr)
    print(f" EHRSQL Aggregate ({n_trials} trials, {sums['total']} tasks)", file=sys.stderr)
    print(f"  Execution F1:      {result['f1_exec']}%", file=sys.stderr)
    print(f"  Execution Prec:    {result['precision_exec']}%", file=sys.stderr)
    print(f"  Execution Recall:  {result['recall_exec']}%", file=sys.stderr)
    print(f"  Answer F1:         {result['f1_ans']}%", file=sys.stderr)
    print(f"  Answer Prec:       {result['precision_ans']}%", file=sys.stderr)
    print(f"  Answer Recall:     {result['recall_ans']}%", file=sys.stderr)
    print(f"  Pass@1:            {result['pass_at_1']}", file=sys.stderr)
    print(f"  Passed:            {sums['passed']}/{sums['total']}", file=sys.stderr)
    print(f"  Filled:            {sums['filled']}/{sums['total']} ({result['fill_rate']:.1%})", file=sys.stderr)
    print(f"{'='*44}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
