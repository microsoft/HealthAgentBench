#!/usr/bin/env python3
"""Generate Harbor tasks for the MIMIC-CXR report **correction** benchmark.

Each task is one patient. Unlike ``xray_report_gen`` where the agent must
*generate* FINDINGS from scratch, here the agent sees a pre-populated DRAFT
FINDINGS in the target study's report.txt and must **review and correct** it.
The draft contains deliberate clinical errors derived by opposite-meaning
word/phrase swaps from the real gold FINDINGS (e.g., right→left, mild→severe,
"no consolidation"→"focal consolidation"). The corrected FINDINGS is scored
against the gold by the same CheXprompt-based judge used in xray_report_gen,
but only FINDINGS is scored (no IMPRESSION expected).

This script imports ``scripts/xray_report_gen/generate_harbor_tasks.py`` as
its base and overrides exactly three functions:

  * ``_generate_instruction_md``  — correction-focused instruction
  * ``_build_task_manifest``       — embed the per-case counterfactual draft
  * ``_generate_bootstrap_sh``     — append the draft FINDINGS to the
                                     target study's report.txt
  * ``_copy_evaluator``            — copy this task's FINDINGS-only verifier
                                     instead of xray_report_gen's

Usage:
    uv run python scripts/xray_report_correction/generate_harbor_tasks.py \\
        --curated --purge --output-root tasks/xray_report_correction

See ``.agent/plans/xray_report_correction.md`` for the full design.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

# Self-contained: import our local copies of normalization.py and the
# upstream generator (snapshotted into ``_generator_base.py``). No
# runtime dependency on the xray_report_gen sibling directory, so
# deleting it won't break this task.
_LOCAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_LOCAL_DIR))
import _generator_base as _gen_base  # noqa: E402

# Re-export CURATED_CASES so users can refer to the same 10 patients in
# both task variants. The (case_id, subject_id, target_study_id) tuples
# are identical; only the agent's task changes.
CURATED_CASES = _gen_base.CURATED_CASES

# Capture the originals BEFORE we monkey-patch so our overrides can
# delegate to them without infinite recursion.
_orig_build_task_manifest = _gen_base._build_task_manifest
_orig_generate_bootstrap_sh = _gen_base._generate_bootstrap_sh


# ---------------------------------------------------------------------------
# Per-case counterfactual draft FINDINGS.
#
# Each entry is the case's REAL gold FINDINGS with opposite-meaning word
# swaps applied in place. Swaps are restricted to six principle categories
# (anything outside these is left unchanged so we don't penalize agents
# for finding-type ambiguities that aren't testable from the image alone):
#
#   P1. LATERALIZATION             — left ↔ right
#   P2. SEVERITY MODIFIER          — mild ↔ severe, normal ↔ enlarged,
#                                    borderline ↔ markedly,
#                                    minor ↔ extensive, hyper- ↔ hypo-,
#                                    appropriate ↔ inappropriate,
#                                    intact ↔ disrupted, elevation ↔
#                                    depression, increased ↔ decreased
#                                    (degree-of-state modifiers)
#   P3. COMPARISON-WORD FLIP       — when gold uses a comparison verb
#                                    (worsened/improved/persistent/
#                                    resolved/similar), swap to its
#                                    opposite
#   P4. NO-PRIOR / NO-CHANGE       — when gold says "no previous
#       → INTRODUCE CHANGE           images" / "no prior study", swap
#                                    to "prior study available, X has
#                                    changed"; when gold says
#                                    "unchanged" / "stable" / "no
#                                    change", flip to "worsened" /
#                                    "improved" / "has changed"
#   P5. COUNT CHANGE               — "three chest tubes" ↔ "two"
#   P6. LOCATION CHANGE            — upper ↔ lower lobe, aortic arch ↔
#                                    mitral valve, above ↔ below
#                                    diaphragm, mid ↔ proximal SVC, etc.
#   P7. EXPLICIT NEGATION OF       — when gold explicitly states a
#       FINDING → ADD THE FINDING    finding is absent ("no
#                                    consolidation", "no pleural
#                                    effusion", "no pneumothorax"),
#                                    flip the negation to assert
#                                    presence ("focal consolidation
#                                    seen"). Only applies when gold
#                                    NEGATES — do not add findings gold
#                                    is silent about.
#
# DELIBERATELY OUT OF SCOPE (do NOT inject):
#   * MEASUREMENT CHANGES           — numeric distances hard to verify
#                                     from images (e.g., 4.8 cm ETT
#                                     position kept verbatim).
#   * ACUITY SWAPS                  — acute ↔ chronic, old healed ↔ acute
#                                     are temporal/diagnostic categories,
#                                     not severity per se.
#   * DIAGNOSTIC CATEGORY SWAPS     — atelectasis ↔ consolidation,
#                                     pneumonia ↔ edema — multiple
#                                     interpretations of the same image
#                                     can be defensible.
#   * REMOVAL OF FINDINGS           — turning gold's POSITIVE finding
#                                     into "no X" (the inverse of P7)
#                                     risks penalizing real findings
#                                     the radiologist chose to mention.
#                                     P7 only ADDS findings; never
#                                     REMOVES them.
#   * ADDITIVE FINDINGS             — adding a finding gold didn't
#                                     mention at all (e.g., "intact" →
#                                     "old healed rib fracture") —
#                                     gold may have legitimately
#                                     omitted it. Distinct from P7
#                                     which only flips explicit
#                                     negations.
#
# Diff each entry against the corresponding gold in
# ``tasks/xray_report_correction/case_<NN>/tests/target_report.txt``.
# ---------------------------------------------------------------------------
SWAP_RULES: dict[str, list[tuple[str, str]]] = {
    # case_01 — 4 swaps (P2 / P6 / P7 / P2)
    "case_01": [
        ("hyperinflated", "hypoinflated"),
        ("upper lobe", "lower lobe"),
        ("No focal consolidation, effusion, or pneumothorax seen",
         "Focal consolidation, pleural effusion, and pneumothorax seen"),
        ("silhouette is normal", "silhouette is enlarged"),
    ],
    # case_02 — 3 swaps (P3 / P6 / P7)
    "case_02": [
        ("cardiomegaly is similar", "cardiomegaly has worsened"),
        ("aortic arch", "mitral valve"),
        ("without evidence of overt pulmonary edema",
         "with evidence of overt pulmonary edema"),
    ],
    # case_03 — 7 swaps (P5 / P1 / P3 / P2 / P7 / P3 / P1)
    "case_03": [
        ("three chest tubes", "two chest tubes"),
        ("the right hemithorax", "the left hemithorax"),
        ("is unchanged as compared", "is worsened as compared"),
        ("increased gas filling", "decreased gas filling"),
        ("No current evidence of pneumothorax",
         "Small pneumothorax is present"),
        ("Unchanged normal appearance", "Worsened appearance"),
        ("of the left lung", "of the right lung"),
    ],
    # case_04 — 8 swaps (P2 / P2 / P6 / P6 / P2+P1+P3 / P2 / P3 / P7)
    # Note: numeric measurements (4.8 cm, 2.6 cm) deliberately preserved.
    "case_04": [
        ("and is appropriate in position", "and is inappropriate in position"),
        ("with intact sternal sutures", "with disrupted sternal sutures"),
        ("below the diaphragm", "above the diaphragm"),
        ("into the stomach", "into the esophagus"),
        ("Asymmetric, mild, right pulmonary edema has improved",
         "Asymmetric, severe, left pulmonary edema has worsened"),
        ("Normal heart size", "Enlarged heart size"),
        ("hilar contours are unchanged", "hilar contours have worsened"),
        ("There is no pleural effusion",
         "There is small bilateral pleural effusion"),
    ],
    # case_05 — 5 swaps (P3 / P2+P3 / P7 / P1 / P3)
    "case_05": [
        ("marked improvement", "marked worsening"),
        ("Unchanged borderline size", "Worsened, markedly enlarged size"),
        ("No pleural effusions", "Bilateral pleural effusions"),
        ("right internal jugular", "left internal jugular"),
        ("in constant position", "in changing position"),
    ],
    # case_06 — 4 swaps (P1 / P6 / P7 / P2). NB: source phrase
    # "at in mid SVC" matches a typo in the gold report.
    "case_06": [
        ("Right PICC", "Left PICC"),
        ("at in mid SVC", "at the proximal SVC"),
        ("There is no consolidation, pleural effusion, or pneumothorax",
         "There is focal consolidation, a small left pleural effusion, but no pneumothorax"),
        ("silhouettes are normal size", "silhouettes are enlarged"),
    ],
    # case_07 — 3 swaps (P2 / P3 / P3)
    "case_07": [
        ("remains enlarged", "remains normal in size"),
        ("persistent pulmonary vascular", "resolving pulmonary vascular"),
        ("appears similar compared", "appears worsened compared"),
    ],
    # case_08 — 4 swaps (P4 / P2 / P7 / P1)
    "case_08": [
        ("No previous images.",
         "Multiple priors available; lung volumes have worsened from prior."),
        ("mild hyperexpansion", "severe hyperexpansion"),
        ("However, no evidence of acute pneumonia, vascular congestion, or pleural effusion.",
         "However, evidence of acute pneumonia, vascular congestion, and a small pleural effusion is present."),
        ("on the right", "on the left"),
    ],
    # case_09 — 7 swaps (P2 / P2+P1 / P1 / P2 / P7 / P3 / P7)
    # NB: source "Re- demonstrated is enlargement" includes a stray
    # space (gold report quirk); CF restores standard "Re-demonstrated".
    "case_09": [
        ("Re- demonstrated is enlargement",
         "Re-demonstrated is normal size"),
        ("elevation of the right hemidiaphragm",
         "depression of the left hemidiaphragm"),
        ("the left lung base", "the right lung base"),
        ("underpenetration", "overpenetration"),
        ("although no definite focal consolidation is seen",
         "although definite focal consolidation is seen"),
        ("Pulmonary edema persists", "Pulmonary edema has resolved"),
        ("No large pleural effusion seen", "Large pleural effusion seen"),
    ],
    # case_10 — 6 swaps (P7 / P2 / P7 / P4 / P1 / P1).
    # The gold has both "LEFT HEMIDIAPHRAGM" (radiopaque structure) and
    # "LEFT MID HEMITHORAX" (surgical clips). The two swaps below target
    # them separately; the second "AND UPPER HEMITHORAX" stays neutral.
    "case_10": [
        ("NO FOCAL CONSOLIDATION IS SEEN",
         "FOCAL CONSOLIDATION IS SEEN IN THE RIGHT LOWER LOBE"),
        ("MINOR BASILAR ATELECTASIS", "EXTENSIVE BASILAR ATELECTASIS"),
        ("NO PLEURAL EFFUSION OR PNEUMOTHORAX",
         "MODERATE PLEURAL EFFUSION BUT NO PNEUMOTHORAX"),
        ("ARE STABLE", "HAVE WORSENED FROM PRIOR"),
        ("LEFT HEMIDIAPHRAGM", "RIGHT HEMIDIAPHRAGM"),
        ("LEFT MID HEMITHORAX", "RIGHT MID HEMITHORAX"),
    ],
}


# ---------------------------------------------------------------------------
# Shared helpers used by both the host-side validation tests and the
# bootstrap.sh Python block. Keep these pure functions so the bootstrap
# can inline them verbatim.
# ---------------------------------------------------------------------------
def extract_gold_findings(report_text: str) -> str:
    """Return the FINDINGS section from a full radiology report.

    Preserves paragraph breaks as ``\\n\\n`` while collapsing intra-
    paragraph whitespace (line wraps, indents) to single spaces. This is
    the canonical form that ``SWAP_RULES`` source phrases were authored
    against — keep this regex / normalization aligned with the one
    embedded in the generated bootstrap.sh.
    """
    import re as _re
    m = _re.search(
        r'^[\s>]*FINDINGS:\s*(.*?)(?=^[\s>]*(IMPRESSION|NOTIFICATION|RECOMMENDATION):|\Z)',
        report_text,
        flags=_re.MULTILINE | _re.DOTALL,
    )
    if not m:
        raise ValueError("report has no FINDINGS section")
    findings = m.group(1)
    paragraphs = _re.split(r'\n\s*\n', findings)
    normalized: list[str] = []
    for p in paragraphs:
        p_clean = _re.sub(r'\s+', ' ', p).strip()
        if p_clean:
            normalized.append(p_clean)
    return '\n\n'.join(normalized)


def apply_swap_rules(gold_findings: str, rules: list[tuple[str, str]]) -> str:
    """Apply ``rules`` to ``gold_findings`` in order and return the
    counterfactual draft. Each source phrase must appear at least once
    in the current text or we raise — that guarantees rule rot
    (gold-side text drift) fails loudly at bootstrap rather than
    silently producing the gold.
    """
    out = gold_findings
    for src, dst in rules:
        if src not in out:
            raise AssertionError(
                f"swap source phrase missing from FINDINGS: {src!r}"
            )
        out = out.replace(src, dst, 1)
    return out


# ---------------------------------------------------------------------------
# Override 1: instruction.md — correction-focused, FINDINGS-only.
# ---------------------------------------------------------------------------
_INSTRUCTION_TEMPLATE = """# Radiology Report Correction

A draft radiology report for this patient's most recent chest X-ray
study has been prepared by a junior radiologist. The draft is already
populated in the `FINDINGS:` section of the target study's `report.txt`
under `/data/patient/<target_study>/`. The draft might contain
clinical errors — your job is to **review and correct it**.

**Rules:**

1. You may **edit** existing sentences in the draft.
2. The draft should already address the relevant findings — you **may not add** new statements about findings the draft did not
   already mention. 
3. Submit only the corrected FINDINGS section. No IMPRESSION is
   expected.

Use the chest-X-ray images and the prior reports (if any) to determine
the correct findings.

**You have up to 1 hour to complete this task.**

## Workspace layout

All data under `/data/patient/` belongs to a **single patient**. Each
subfolder is one chest-X-ray study for that patient:

```
/data/patient/
    study_01_<timestamp>/
        view_01.jpg
        view_02.jpg
        report.txt          # prior: full report INCLUDING FINDINGS+IMPRESSION
    study_02_<timestamp>/
        ...
    study_NN_<timestamp>/   # TARGET (highest-numbered)
        view_01.jpg
        report.txt          # has EXAMINATION/INDICATION/HISTORY/...
                            # and a DRAFT FINDINGS section to correct
```

- Folder names sort chronologically. The **last** folder (highest
  ``study_NN``) is the TARGET study.
- **Prior** studies' `report.txt` contains the full original report
  (FINDINGS + IMPRESSION + everything else).
- The **target** study's `report.txt` contains the non-generated
  sections (EXAMINATION, INDICATION, HISTORY, TECHNIQUE, COMPARISON)
  followed by a `FINDINGS:` section with the **draft to be corrected**.

## Your output

Set `final_answer` in `/workspace/submission.json` to the corrected
report. **Start with the literal `FINDINGS:` header on its own line,
followed by your corrected body text.** Do not include an IMPRESSION
section — only FINDINGS is scored.

Example:

```
FINDINGS:
The lungs are hyperinflated... [your corrected text]
```

Use a JSON-aware tool to edit `submission.json` (e.g. `python -c "import
json; ..."`); manual string edits easily corrupt the JSON.

You should not cheat and you should not directly look up the end
solutions from the internet.
"""


def _generate_instruction_md(task: dict[str, Any]) -> str:
    """Build the correction-focused instruction. Same across all 10
    cases — the draft is in the per-case report.txt, not in the
    instruction."""
    return _INSTRUCTION_TEMPLATE


# ---------------------------------------------------------------------------
# Override 2: task_manifest.json — add the per-case counterfactual draft.
# ---------------------------------------------------------------------------
def _build_task_manifest(task: dict[str, Any]) -> dict[str, Any]:
    """Extend the base manifest with the per-case phrase-swap rules.

    The manifest is bind-mounted into the bootstrap container only
    (never into main). At bootstrap time the gold report is fetched
    into ``/tests/target_report.txt`` and the ``counterfactual_swap_rules``
    list below is applied to its FINDINGS section to synthesize the
    corrupted draft. Keeping rules (rather than full corrupted text)
    here means a) one place to audit the swaps, and b) the bootstrap
    fails loudly if upstream MIMIC-CXR ever rewords a gold report.
    """
    manifest = _orig_build_task_manifest(task)
    case_id = task["task_id"]
    if case_id not in SWAP_RULES:
        raise KeyError(
            f"task {case_id} has no entry in SWAP_RULES; add one to "
            "scripts/xray_report_correction/generate_harbor_tasks.py."
        )
    # JSON-encode rules as [[src, dst], ...] for the bootstrap reader.
    manifest["counterfactual_swap_rules"] = [
        [src, dst] for src, dst in SWAP_RULES[case_id]
    ]
    return manifest


# ---------------------------------------------------------------------------
# Override 3: bootstrap.sh — append the draft FINDINGS to report.txt.
# ---------------------------------------------------------------------------
def _generate_bootstrap_sh() -> str:
    """Same as xray_report_gen's bootstrap, but with a tail Python block
    that re-opens the target study's report.txt (already written by the
    base bootstrap with the allowlist sections) and appends a
    ``FINDINGS:\\n<counterfactual>\\n`` block.

    Implementation: take the base bootstrap, append our extra Python
    block before the final ``echo / exit 0``. Done as a string-level
    splice so we re-use any future fixes upstream without divergence.
    """
    base = _orig_generate_bootstrap_sh()
    # The base ends with:  echo "[bootstrap] complete."\n  exit 0\n  """
    # Splice the counterfactual write step in just before that.
    extra = """
# Synthesize the counterfactual DRAFT FINDINGS from the gold report at
# /tests/target_report.txt by applying the swap rules embedded in the
# manifest, then append the result to the target study's report.txt.
# The agent loading report.txt will see a populated FINDINGS section
# to review and correct. The full corrupted text never leaves this
# bootstrap container.
python3 <<'PY'
import json
import re
from pathlib import Path


def _extract_gold_findings(report_text: str) -> str:
    # Keep this aligned with extract_gold_findings() in
    # scripts/xray_report_correction/generate_harbor_tasks.py.
    m = re.search(
        r'^[\\s>]*FINDINGS:\\s*(.*?)(?=^[\\s>]*(IMPRESSION|NOTIFICATION|RECOMMENDATION):|\\Z)',
        report_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not m:
        raise ValueError("gold report has no FINDINGS section")
    paragraphs = re.split(r'\\n\\s*\\n', m.group(1))
    normalized = []
    for p in paragraphs:
        p_clean = re.sub(r'\\s+', ' ', p).strip()
        if p_clean:
            normalized.append(p_clean)
    return '\\n\\n'.join(normalized)


def _apply_swap_rules(text: str, rules):
    for src, dst in rules:
        if src not in text:
            raise AssertionError(
                f"swap source phrase missing from FINDINGS: {src!r}"
            )
        text = text.replace(src, dst, 1)
    return text


manifest = json.loads(Path("/opt/task_manifest.json").read_text())
rules = manifest.get("counterfactual_swap_rules") or []
if not rules:
    print("[bootstrap] no counterfactual_swap_rules in manifest; skipping append.")
else:
    gold_path = Path("/tests/target_report.txt")
    if not gold_path.is_file() or gold_path.stat().st_size == 0:
        raise SystemExit(
            "[bootstrap] /tests/target_report.txt missing or empty — cannot "
            "synthesize counterfactual draft. Check PhysioNet credentials and "
            "that the report fetch earlier in this bootstrap succeeded."
        )
    gold_findings = _extract_gold_findings(gold_path.read_text())
    draft = _apply_swap_rules(gold_findings, rules)
    dest = Path("/data/patient")
    for study in manifest["studies"]:
        if study.get("is_target"):
            rp = dest / study["folder"] / "report.txt"
            existing = rp.read_text() if rp.exists() else ""
            block = "\\nFINDINGS:\\n" + draft + "\\n"
            rp.write_text(existing.rstrip() + block)
            print(
                f"[bootstrap] synthesized DRAFT FINDINGS via {len(rules)} swaps "
                f"({len(draft)} chars) into {rp}"
            )
            break
PY

"""
    needle = 'echo "[bootstrap] complete."'
    if needle not in base:
        raise RuntimeError(
            "Could not locate splice point in xray_report_gen bootstrap "
            "template. The upstream template may have changed; update the "
            "needle in xray_report_correction/generate_harbor_tasks.py."
        )
    return base.replace(needle, extra + needle, 1)


# ---------------------------------------------------------------------------
# Override 4: harbor_evaluator — use our FINDINGS-only version.
# ---------------------------------------------------------------------------
def _copy_evaluator(tests_dir: Path) -> None:
    """Copy this task's FINDINGS-only evaluator into tests/."""
    src = Path(__file__).resolve().parent / "harbor_evaluator.py"
    shutil.copyfile(src, tests_dir / "harbor_evaluator.py")


# ---------------------------------------------------------------------------
# Wire up the overrides by monkey-patching the base module's namespace.
# ``_write_single_task`` reads these symbols from its own module's
# globals, so reassigning them here affects every per-case build.
# ---------------------------------------------------------------------------
_gen_base._generate_instruction_md = _generate_instruction_md
_gen_base._build_task_manifest = _build_task_manifest
_gen_base._generate_bootstrap_sh = _generate_bootstrap_sh
_gen_base._copy_evaluator = _copy_evaluator


# ---------------------------------------------------------------------------
# Entry point — delegate to the base's main() with our overrides active.
# ---------------------------------------------------------------------------
def main() -> None:
    # Base ``main`` reads sys.argv directly via argparse — no arg needed.
    return _gen_base.main()


if __name__ == "__main__":
    main()
