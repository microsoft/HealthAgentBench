"""Per-volume verifier for the ct_abnormality benchmark.

Each task scores one chest-CT volume. The agent's submission at
``/workspace/submission/predictions.txt`` contains one ``label: yes/no``
line per requested label (the labels are listed at
``/workspace/data/labels.txt`` — only the labels whose value is
unambiguously grounded in the paired physician report for that volume).

Gold labels are pinned at ``/tests/gold.json`` per task and are derived from
the radiology report under a strict exact-wording rule (see
``scripts/ct_abnormality/assets/manifest.yaml`` and ``.agent/plans/ct_abnormality.md``).

Reward is **binary**: ``1.0`` iff every requested label is correct,
``0.0`` otherwise. Per-volume diagnostic accuracy and per-label TP/FP/FN
are also written to ``reward.json`` for the cross-volume aggregator.

Output files written to ``log_dir`` (= ``/logs/verifier`` in Harbor):

- ``metrics.json`` — full diagnostic payload (per-label predicted/gold/match,
  evidence quote, accuracy).
- ``reward.json`` — flat ``dict[str, float|int|list]`` Harbor reads.

``reward.txt`` is **not** written — Harbor reads ``reward.txt`` first when
present, which masks the rich payload.

Per the existing pattern in ``scripts/clinical_trial_matching/``, the per-trial
``success`` field is intentionally absent from ``reward.json`` so the launcher's
``--metric-to-report success`` falls back to the aggregate-level integer count.
The binary 0.0/1.0 reward is what Harbor reads for its ``Successes`` column.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_TRUE_TOKENS = frozenset({"yes", "y", "true", "t", "1", "positive", "pos"})
_FALSE_TOKENS = frozenset({"no", "n", "false", "f", "0", "negative", "neg"})


def _sanitize(name: str) -> str:
    """Convert a disease label to a flat metric-key suffix.

    Lower-case, alphanumeric + underscore only. Must match the identical
    helper in ``scripts/ct_abnormality/aggregate_metric.py`` so the
    ``gold_<suffix>`` / ``pred_<suffix>`` keys written here line up with the
    ``f1_<suffix>`` keys the aggregator emits.
    """
    s = name.lower().replace("/", " ").replace("-", " ")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


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


def _parse_predictions(path: Path) -> dict[str, int]:
    """Parse ``label: yes|no`` lines into a ``{label_name_lower: 0|1}`` dict.

    Tolerates blank lines, ``#`` comments, and CSV padding. Splits on the
    first ``:``. Returns ``{}`` if the file is missing or empty.
    Predictions whose value cannot be parsed as yes/no are skipped — the
    verifier will then count that label as wrong (no-prediction).
    """
    if not path.exists():
        return {}
    out: dict[str, int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        name, _, value = line.partition(":")
        name = name.strip().lower()
        token = value.strip().split(",")[0].strip().lower()
        if not name or not token:
            continue
        if token in _TRUE_TOKENS:
            out[name] = 1
        elif token in _FALSE_TOKENS:
            out[name] = 0
        else:
            continue
    return out


def evaluate(
    submission_path: Path,
    gold_path: Path,
    log_dir: Path,
    turn_count_override: int | None = None,
) -> float:
    """Score the agent's predictions against the per-volume gold.

    Returns the binary reward (1.0 if all retained labels match, 0.0
    otherwise). Always writes ``metrics.json`` and ``reward.json`` to
    ``log_dir``; never raises on bad agent input — writes
    ``verifier_error.txt`` instead and returns 0.0.
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        (log_dir / "verifier_error.txt").write_text(
            f"failed to read gold at {gold_path}: {exc!r}\n"
        )
        return 0.0

    volume_name: str = gold.get("volume_name", "")
    gold_labels: list[dict[str, Any]] = gold.get("labels", [])
    if not gold_labels:
        (log_dir / "verifier_error.txt").write_text(
            f"gold has no labels: {gold_path}\n"
        )
        return 0.0

    predictions = _parse_predictions(submission_path)
    if not predictions:
        (log_dir / "verifier_error.txt").write_text(
            f"submission file at {submission_path} missing, empty, or unparseable\n"
        )

    per_label: list[dict[str, Any]] = []
    # Flat per-disease keys (gold_<suffix> / pred_<suffix>) carried in reward.json
    # so the aggregator can rebuild per-disease F1 from the flat reward stream
    # Harbor feeds it (Harbor's uv-script metric hands the aggregator only the
    # flat reward.json contents — never the rich per_label in metrics.json).
    per_disease_flat: dict[str, int] = {}
    n_correct = 0
    tp = fp = tn = fn = 0
    for entry in gold_labels:
        name = str(entry["name"])
        gold_value = int(entry["gold"])
        evidence = str(entry.get("evidence", ""))
        pred = predictions.get(name.lower())
        match = pred is not None and pred == gold_value
        suffix = _sanitize(name)
        if suffix:
            per_disease_flat[f"gold_{suffix}"] = gold_value
            # -1 encodes "no parseable prediction" (None) as a flat int.
            per_disease_flat[f"pred_{suffix}"] = pred if pred is not None else -1
        if match:
            n_correct += 1
            if gold_value == 1:
                tp += 1
            else:
                tn += 1
        else:
            if gold_value == 1:
                fn += 1
            else:
                # If the agent didn't submit, count as FN-of-prediction (i.e.
                # missed a negative call). For per-disease F1 we treat
                # missing-prediction as the *opposite* of gold so it always
                # counts as wrong, but for confusion-matrix purposes a missing
                # prediction on a gold-negative is FP only if the agent actually
                # said "yes". If pred is None we put it in FN bucket.
                if pred == 1:
                    fp += 1
                else:
                    fn += 1
        per_label.append(
            {
                "name": name,
                "gold": gold_value,
                "predicted": pred,
                "match": bool(match),
                "evidence": evidence,
            }
        )

    n_retained = len(gold_labels)
    accuracy = n_correct / n_retained if n_retained else 0.0
    success = 1 if n_correct == n_retained else 0
    reward = float(success)

    if turn_count_override is not None:
        turn_count: int | None = turn_count_override
    else:
        turn_count = _read_turn_count()

    metrics: dict[str, Any] = {
        "volume_name": volume_name,
        "reward": reward,
        "accuracy": accuracy,
        "n_retained": n_retained,
        "n_correct": n_correct,
        "n_true_positives": tp,
        "n_true_negatives": tn,
        "n_false_positives": fp,
        "n_false_negatives": fn,
        "per_label": per_label,
        "turn_count": turn_count,
    }
    (log_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # Harbor's VerifierResult pydantic schema requires every value in
    # reward.json's `rewards` dict to be float | int. Strings and nested
    # lists/dicts cause Harbor to raise ValidationError after the verifier
    # has already run, which cascades into a launcher crash. So we keep
    # reward.json strictly flat-scalar; the rich payload (per_label
    # breakdown + volume_name) lives in metrics.json, and the aggregator
    # reads metrics.json for the per-disease F1 it needs.
    reward_payload: dict[str, float | int] = {
        "reward": reward,
        "accuracy": accuracy,
        "n_retained": n_retained,
        "n_correct": n_correct,
        "n_true_positives": tp,
        "n_true_negatives": tn,
        "n_false_positives": fp,
        "n_false_negatives": fn,
        "turn_count": int(turn_count) if turn_count is not None else -1,
    }
    # Per-disease gold/pred as flat ints — lets the aggregator compute
    # macro/micro/per-disease F1 from reward.json alone (see note above).
    reward_payload.update(per_disease_flat)
    (log_dir / "reward.json").write_text(json.dumps(reward_payload, indent=2))
    return reward


def main() -> None:
    submission = Path("/workspace/submission/predictions.txt")
    gold = Path("/tests/gold.json")
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, gold, log_dir)
    print(f"reward={score:.6f}")


if __name__ == "__main__":
    main()
