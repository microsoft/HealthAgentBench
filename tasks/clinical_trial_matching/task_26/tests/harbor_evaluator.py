"""Ranking verifier for the clinical_trial_matching benchmark.

Each task scores one patient topic. The agent's submission at
``/workspace/submission/ranked_trials.txt`` is a plain text file with
one trial NCT identifier per line, ordered most-confident-first
(rank 1 = highest confidence the patient is eligible).

The verifier loads the per-topic ``qrels.txt`` (graded judgments
``topic 0 nct grade`` with grades 0=non-relevant, 1=excluded, 2=eligible)
and computes:

- **NDCG@10** (TREC-CDS standard, linear gain):
  DCG@10 = sum_{i=1..10} grade_i / log2(i + 1)
  IDCG@10 = DCG@10 of the optimal ordering of the judged set.
  NDCG@10 = DCG@10 / IDCG@10. **NDCG@10 is the reward.**
- **DCG@10** (raw, unnormalized).
- **Set-based diagnostics** computed over the full submitted list
  treating it as the eligibility prediction:
  precision/recall/F1 against grade=2 (eligible) gold.

Output files written to ``log_dir``:

- ``metrics.json`` — full diagnostic payload.
- ``reward.json`` — flat ``dict[str, float|int]`` Harbor reads.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


K_TOP = 10


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


def _load_qrels(path: Path) -> tuple[int | None, dict[str, int]]:
    """Parse a TREC qrels file; return (topic_id, {nct_id: grade})."""
    topic_id: int | None = None
    grades: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        try:
            t = int(parts[0])
            g = int(parts[3])
        except ValueError:
            continue
        if topic_id is None:
            topic_id = t
        grades[parts[2]] = g
    return topic_id, grades


def _load_ranking(path: Path) -> list[str]:
    """Parse the agent's ranked submission. One NCT_ID per line, ranked
    most-confident-first. Strip blanks and ``#`` comments. Take the first
    whitespace/comma token of each row. De-duplicate while preserving the
    first occurrence (highest rank wins).
    """
    if not path.exists():
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        token = line.split()[0].split(",")[0].strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _dcg_at_k(grades: list[int], k: int) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(grades[:k]))


def _ideal_dcg_at_k(qrels_grades: list[int], k: int) -> float:
    ideal = sorted(qrels_grades, reverse=True)
    return _dcg_at_k(ideal, k)


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def evaluate(
    submission_path: Path,
    qrels_path: Path,
    log_dir: Path,
    turn_count_override: int | None = None,
) -> float:
    """Score the agent's ranked submission. Returns NDCG@10."""
    log_dir.mkdir(parents=True, exist_ok=True)

    topic_id, qrels = _load_qrels(qrels_path)
    if not qrels:
        (log_dir / "verifier_error.txt").write_text(
            f"qrels file is empty or unparseable: {qrels_path}\n"
        )
        return 0.0

    eligible: set[str] = {nct for nct, g in qrels.items() if g == 2}
    excluded: set[str] = {nct for nct, g in qrels.items() if g == 1}
    nonrel: set[str] = {nct for nct, g in qrels.items() if g == 0}

    ranking = _load_ranking(submission_path)
    if not ranking:
        (log_dir / "verifier_error.txt").write_text(
            f"submission file at {submission_path} missing or empty\n"
        )

    # Graded relevance for the agent's ranked list. Anything not in qrels
    # is treated as grade 0 (non-judged ⇒ no gain).
    ranked_grades = [qrels.get(nct, 0) for nct in ranking]
    dcg10 = _dcg_at_k(ranked_grades, K_TOP)
    idcg10 = _ideal_dcg_at_k(list(qrels.values()), K_TOP)
    ndcg10 = dcg10 / idcg10 if idcg10 > 0 else 0.0

    # Set-based diagnostics over the full submitted ranking.
    pred_set = set(ranking)
    tp = pred_set & eligible
    fp_excluded = pred_set & excluded
    fp_nonrel = pred_set & nonrel
    fp_unjudged = pred_set - eligible - excluded - nonrel
    fn = eligible - pred_set
    n_pred = len(pred_set)
    n_tp = len(tp)
    n_fp = len(fp_excluded) + len(fp_nonrel) + len(fp_unjudged)
    precision = n_tp / n_pred if n_pred > 0 else 0.0
    recall = n_tp / len(eligible) if eligible else 0.0
    f1 = _f1(precision, recall)

    # Top-K precision/recall (rank-aware diagnostic alongside NDCG@10).
    top_k_set = set(ranking[:K_TOP])
    n_top_k = len(top_k_set)
    n_top_k_tp = len(top_k_set & eligible)
    p_at_k = n_top_k_tp / n_top_k if n_top_k > 0 else 0.0
    r_at_k = n_top_k_tp / len(eligible) if eligible else 0.0

    if turn_count_override is not None:
        turn_count: int | None = turn_count_override
    else:
        turn_count = _read_turn_count()

    metrics: dict[str, Any] = {
        "topic_id": topic_id,
        "ndcg_at_10": ndcg10,
        "dcg_at_10": dcg10,
        "idcg_at_10": idcg10,
        "precision_at_10": p_at_k,
        "recall_at_10": r_at_k,
        "f1": f1,
        "precision": precision,
        "recall": recall,
        "n_ranked": len(ranking),
        "n_predicted": n_pred,
        "n_eligible": len(eligible),
        "n_excluded": len(excluded),
        "n_nonrelevant": len(nonrel),
        "n_true_positives": n_tp,
        "n_false_positives": n_fp,
        "n_false_negatives": len(fn),
        "n_fp_excluded": len(fp_excluded),
        "n_fp_nonrelevant": len(fp_nonrel),
        "n_fp_unjudged": len(fp_unjudged),
        "turn_count": turn_count,
    }
    (log_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    reward_payload: dict[str, float | int] = {
        "reward": ndcg10,
        "ndcg_at_10": ndcg10,
        "dcg_at_10": dcg10,
        "idcg_at_10": idcg10,
        "precision_at_10": p_at_k,
        "recall_at_10": r_at_k,
        "f1": f1,
        "precision": precision,
        "recall": recall,
        "n_ranked": len(ranking),
        "n_predicted": n_pred,
        "n_eligible": len(eligible),
        "n_excluded": len(excluded),
        "n_nonrelevant": len(nonrel),
        "n_true_positives": n_tp,
        "n_false_positives": n_fp,
        "n_false_negatives": len(fn),
        "n_fp_excluded": len(fp_excluded),
        "n_fp_nonrelevant": len(fp_nonrel),
        "n_fp_unjudged": len(fp_unjudged),
        "turn_count": int(turn_count) if turn_count is not None else -1,
        "topic_id": int(topic_id) if topic_id is not None else -1,
    }
    (log_dir / "reward.json").write_text(json.dumps(reward_payload, indent=2))
    return ndcg10


def main() -> None:
    submission = Path("/workspace/submission/ranked_trials.txt")
    qrels = Path("/tests/qrels.txt")
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, qrels, log_dir)
    print(f"ndcg_at_10={score:.6f}")


if __name__ == "__main__":
    main()
