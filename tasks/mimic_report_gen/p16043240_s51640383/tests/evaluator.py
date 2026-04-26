"""Evaluator for MIMIC-CXR report generation tasks.

Compares agent-generated reports against ground-truth reports using
text-overlap metrics (BLEU, ROUGE-L) and a fill-rate check.

This module is copied into each task's tests/ directory at generation time.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


_SECTION_RE = re.compile(
    r"\b(findings|impression)\s*:\s*", flags=re.IGNORECASE
)


def _split_findings_impression(text: str) -> tuple[str, str]:
    """Parse FINDINGS and IMPRESSION bodies out of a free-text answer.

    Returns (findings_body, impression_body), each stripped of leading/trailing
    whitespace. Missing sections come back as empty strings.
    """
    if not text:
        return "", ""
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return "", ""
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections.get("FINDINGS", ""), sections.get("IMPRESSION", "")


def _normalize_report(text: str) -> str:
    """Normalize a radiology answer for comparison.

    Steps:
      - strip leading/trailing whitespace from the whole answer
      - drop the "FINAL REPORT" boilerplate header if present
      - parse out FINDINGS and IMPRESSION bodies, strip each, then re-emit
        in canonical form so spacing around the section labels never affects
        the comparison
      - if section headers are absent, fall back to plain whitespace
        normalization so we still get *some* signal
      - lowercase and collapse internal whitespace
    """
    text = text.strip()
    text = re.sub(r"^\s*final report\s*", "", text, flags=re.IGNORECASE)

    findings, impression = _split_findings_impression(text)
    if findings or impression:
        canonical = f"FINDINGS:\n{findings}\n\nIMPRESSION:\n{impression}"
    else:
        canonical = text

    canonical = canonical.lower()
    canonical = re.sub(r"\s+", " ", canonical).strip()
    return canonical


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\w+", text.lower())


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _bleu_score(reference: str, hypothesis: str, max_n: int = 4) -> float:
    """Compute corpus-level BLEU (single pair) up to max_n-grams.

    Uses brevity penalty and clipped n-gram precision.
    """
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)

    if not hyp_tokens or not ref_tokens:
        return 0.0

    # Brevity penalty
    bp = min(1.0, len(hyp_tokens) / len(ref_tokens)) if ref_tokens else 0.0

    log_avg = 0.0
    import math

    for n in range(1, max_n + 1):
        ref_ng = Counter(_ngrams(ref_tokens, n))
        hyp_ng = Counter(_ngrams(hyp_tokens, n))
        if not hyp_ng:
            return 0.0
        clipped = sum(min(hyp_ng[ng], ref_ng[ng]) for ng in hyp_ng)
        precision = clipped / sum(hyp_ng.values())
        if precision == 0:
            return 0.0
        log_avg += math.log(precision) / max_n

    return bp * math.exp(log_avg)


def _rouge_l_f1(reference: str, hypothesis: str) -> float:
    """Compute ROUGE-L F1 score using longest common subsequence."""
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)

    if not ref_tokens or not hyp_tokens:
        return 0.0

    # LCS length via DP
    m, n = len(ref_tokens), len(hyp_tokens)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_len = dp[m][n]
    if lcs_len == 0:
        return 0.0

    precision = lcs_len / n
    recall = lcs_len / m
    f1 = 2 * precision * recall / (precision + recall)
    return f1


def evaluate_single(
    predicted: str,
    expected: str,
) -> dict[str, Any]:
    """Evaluate a single predicted report against the ground truth.

    Returns:
        Dict with bleu, rouge_l, filled, and normalized texts.
    """
    filled = bool(predicted and predicted.strip())
    if not filled:
        return {
            "bleu": 0.0,
            "rouge_l": 0.0,
            "filled": False,
        }

    norm_pred = _normalize_report(predicted)
    norm_expected = _normalize_report(expected)

    return {
        "bleu": _bleu_score(norm_expected, norm_pred),
        "rouge_l": _rouge_l_f1(norm_expected, norm_pred),
        "filled": True,
    }


def evaluate_submission_rows(
    submission: list[dict[str, Any]],
    answer_key: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate all submission rows against the answer key.

    Args:
        submission: List of submission dicts with task_id and final_answer.
        answer_key: List of answer key dicts with task_id and expected_answer.

    Returns:
        Evaluation result dict with aggregate and per-task metrics.
    """
    # Index answer key by task_id
    key_by_id = {k["task_id"]: k for k in answer_key}

    results = []
    total_bleu = 0.0
    total_rouge = 0.0
    filled_count = 0

    for row in submission:
        task_id = row["task_id"]
        predicted = row.get("final_answer", "")
        key_entry = key_by_id.get(task_id)

        if key_entry is None:
            results.append(
                {
                    "task_id": task_id,
                    "error": "No answer key found",
                    "bleu": 0.0,
                    "rouge_l": 0.0,
                    "filled": False,
                }
            )
            continue

        expected = key_entry["expected_answer"]
        metrics = evaluate_single(predicted, expected)
        metrics["task_id"] = task_id

        results.append(metrics)
        total_bleu += metrics["bleu"]
        total_rouge += metrics["rouge_l"]
        if metrics["filled"]:
            filled_count += 1

    total = len(submission)
    return {
        "total_tasks": total,
        "filled_tasks": filled_count,
        "avg_bleu": total_bleu / total if total else 0.0,
        "avg_rouge_l": total_rouge / total if total else 0.0,
        "fill_rate": filled_count / total if total else 0.0,
        "results": results,
    }
