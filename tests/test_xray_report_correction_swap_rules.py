"""Phrase-swap rule audit for ``xray_report_correction``.

These tests guard the contract between ``SWAP_RULES`` (hardcoded in
``scripts/xray_report_correction/generate_harbor_tasks.py``) and the
gold MIMIC-CXR reports committed under
``tasks/xray_report_correction/case_*/tests/target_report.txt``.

Behavior under test:

1. ``apply_swap_rules`` applied to each case's gold FINDINGS produces a
   non-empty draft and consumes every source phrase exactly once — so
   the bootstrap cannot silently regenerate the gold if a rule rots.
2. Within a single case, no rule's source phrase is a substring of any
   other rule's destination phrase. This guards against the
   apply-in-order trap where an earlier swap's output could be matched
   by a later swap's source pattern.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts" / "xray_report_correction"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_harbor_tasks import (  # noqa: E402
    SWAP_RULES,
    apply_swap_rules,
    extract_gold_findings,
)


@pytest.mark.parametrize("case_id", sorted(SWAP_RULES))
def test_swap_rules_apply_cleanly_to_committed_gold(case_id: str):
    """Each (gold_phrase → cf_phrase) rule must match the current gold
    report exactly once, and the result must differ from the gold."""
    target_report = REPO_ROOT / "tasks" / "xray_report_correction" / case_id / "tests" / "target_report.txt"
    if not target_report.is_file() or target_report.stat().st_size == 0:
        pytest.skip(f"{case_id} gold not staged — bootstrap fetches at runtime")

    gold = extract_gold_findings(target_report.read_text())
    rules = SWAP_RULES[case_id]
    draft = apply_swap_rules(gold, rules)

    assert draft, f"{case_id} produced empty draft"
    assert draft != gold, f"{case_id} draft == gold (no swaps applied?)"


@pytest.mark.parametrize("case_id", sorted(SWAP_RULES))
def test_no_overlapping_swaps_within_case(case_id: str):
    """Within a single case, no rule's source phrase may be a substring
    of any other rule's destination phrase. That ordering trap would let
    rule N silently re-match a swap made by an earlier rule, producing
    surprising drafts when rules are reordered.
    """
    rules = SWAP_RULES[case_id]
    for i, (src_i, _) in enumerate(rules):
        for j, (_, dst_j) in enumerate(rules):
            if i == j:
                continue
            assert src_i not in dst_j, (
                f"{case_id}: rule[{i}] source phrase {src_i!r} is a substring of "
                f"rule[{j}] destination {dst_j!r} — apply-in-order could re-match"
            )
