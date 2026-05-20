#!/usr/bin/env python3
"""Harbor verifier entry point for MIMIC-CXR report generation.

Called by Harbor after the agent completes. Reads
``/workspace/submission.json``, augments ``tests/task_answer_key.json``
in memory with gold FINDINGS + IMPRESSION parsed from
``/tests/target_report.txt`` (the ``bootstrap`` compose service wrote
this into the host's tests/ dir from PhysioNet before main started;
Harbor mounts it as /tests only at verifier time), then calls
CheXprompt and writes:

  * ``/logs/verifier/reward.json``     — flat scalars Harbor reads:
        ``{reward, n_tasks, n_pass, pass_rate}``
  * ``/logs/verifier/metrics.json``    — same scalars + per-row
        diagnostics (study_id, candidate length, CheXprompt error
        counts by category, pass/fail).

Reward semantics: ``reward = 1.0`` iff every row in the submission has
zero clinically-significant CheXprompt errors; else ``0.0``. For the
1-row-per-trial layout this is identical to ``pass_rate``.

The aggregator at ``scripts/xray_report_gen/aggregate_metric.py``
pools these across trials (mean reward = pass rate across trials;
synthetic-zero for trials with no verifier output).

Required runtime env (verifier process only — agent never sees them):

  * ``OPENAI_API_KEY`` and either ``OPENAI_BASE_URL`` (vanilla OpenAI)
    or ``OPENAI_API_BASE`` + ``OPENAI_API_VERSION`` (Azure).
  * ``CHEXPROMPT_DEPLOYMENT``  — model / deployment name
    (e.g. ``gpt-4-1106-preview``).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Import evaluator from local tests directory (this file is copied next
# to harbor_evaluator.py at task-generation time).
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from harbor_evaluator import evaluate_submission_rows  # type: ignore  # noqa: E402


_SECTION_HEADERS = (
    "EXAMINATION", "INDICATION", "HISTORY", "TECHNIQUE", "COMPARISON",
    "FINDINGS", "IMPRESSION", "RECOMMENDATION", "NOTIFICATION",
)
_SECTION_RE = re.compile(
    r"^[\s>]*(" + "|".join(_SECTION_HEADERS) + r")\s*:\s*",
    flags=re.IGNORECASE | re.MULTILINE,
)


def _parse_sections(text: str) -> dict[str, str]:
    """Tiny MIMIC-CXR section splitter — duplicated here so the verifier
    venv (which only has chexprompt + openai==0.28) doesn't need to import
    the host-side ``normalization`` module."""
    matches = list(_SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections


class MissingGoldError(RuntimeError):
    """Raised when /tests/target_report.txt is missing / empty / has no
    FINDINGS section. This is a VERIFIER failure (bootstrap didn't run
    or didn't fetch the target report), not an agent failure — Harbor
    should surface it in exception_stats so the operator notices."""


def _bootstrap_gold(answer_key, answer_key_path: Path, logs_dir: Path) -> None:
    """For each row whose ``expected_findings`` is empty, parse the
    target's full report (staged at ``/tests/target_report.txt`` by the
    bootstrap compose service) and inject FINDINGS + IMPRESSION into
    the row in memory.

    Raises ``MissingGoldError`` if the gold can't be loaded for any row.
    Surfacing this loudly is important: an agent-side reward of 0 with
    silent "missing gold" would look like a normal failure in Harbor's
    job summary, hiding a verifier / environment bug.

    The augmented answer key is NOT persisted back to disk:
    ``tests/task_answer_key.json`` is the host-side artifact and is kept
    gold-free for redistribution; gold lives only in this Python process
    for the duration of this verifier invocation.
    """
    if isinstance(answer_key, dict):
        rows = [answer_key]
    else:
        rows = list(answer_key)

    target_report_path = Path("/tests/target_report.txt")
    full_text = ""
    if target_report_path.exists():
        try:
            full_text = target_report_path.read_text()
        except OSError as e:
            raise MissingGoldError(
                f"read {target_report_path} failed: {e}"
            ) from e

    if not full_text.strip():
        raise MissingGoldError(
            f"{target_report_path} missing or empty — the bootstrap compose "
            "service should have staged it from PhysioNet. Check that "
            "PN_USER and PN_PASS are set in .env, that PhysioNet is "
            "reachable from the container, and that the bootstrap service "
            "exited 0 before main started."
        )

    sections = _parse_sections(full_text)
    findings = sections.get("FINDINGS", "").strip()
    impression = sections.get("IMPRESSION", "").strip()

    if not findings:
        raise MissingGoldError(
            f"{target_report_path} parsed but has no FINDINGS section "
            f"(impression_len={len(impression)}). The target report may "
            "be malformed; inspect the file inside the container."
        )

    log = []
    for row in rows:
        if (row.get("expected_findings") or "").strip():
            continue
        row["expected_findings"] = findings
        row["expected_impression"] = impression
        log.append(
            f"{row.get('task_id')}: gold injected from {target_report_path} "
            f"({len(findings)} F + {len(impression)} I chars)"
        )
    if log:
        (logs_dir / "gold_bootstrap.log").write_text("\n".join(log) + "\n")


def _write_failure_reward(logs_dir: Path, n_tasks: int, reason: str) -> None:
    """Emit reward.json with reward=0 and a structured failure note."""
    payload = {
        "reward": 0.0,
        "n_tasks": n_tasks,
        "n_pass": 0,
        "pass_rate": 0.0,
        "error": reason,
    }
    (logs_dir / "reward.json").write_text(json.dumps(payload))
    (logs_dir / "metrics.json").write_text(json.dumps(payload, indent=2))


def _parse_submission(raw: str) -> list[dict]:
    """Parse submission.json. Falls back to regex salvage so a minor
    formatting error never zeros the reward without an attempt."""
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []
    except json.JSONDecodeError:
        pass
    # Salvage: scan for task_id / final_answer pairs.
    salvaged: list[dict] = []
    for m in re.finditer(r'"task_id"\s*:\s*"([^"]+)"', raw):
        tid = m.group(1)
        tail = raw[m.end():]
        next_tid = re.search(r'"task_id"\s*:', tail)
        seg = tail[: next_tid.start() if next_tid else len(tail)]
        fa = re.search(r'"final_answer"\s*:\s*"((?:[^"\\]|\\.)*)"', seg, flags=re.DOTALL)
        value = ""
        if fa:
            try:
                value = json.loads(f'"{fa.group(1)}"')
            except Exception:  # noqa: BLE001
                value = fa.group(1)
        salvaged.append({"task_id": tid, "final_answer": value, "payload": None})
    return salvaged


def main() -> int:
    workspace_dir = Path("/workspace")
    tests_dir_path = Path("/tests")
    logs_dir = Path("/logs/verifier")
    logs_dir.mkdir(parents=True, exist_ok=True)

    submission_path = workspace_dir / "submission.json"
    answer_key_path = tests_dir_path / "task_answer_key.json"

    if not submission_path.exists():
        _write_failure_reward(logs_dir, 0, f"submission.json missing: {submission_path}")
        return 1
    if not answer_key_path.exists():
        _write_failure_reward(logs_dir, 0, f"answer key missing: {answer_key_path}")
        return 1

    raw_submission = submission_path.read_text()
    submission = _parse_submission(raw_submission)
    if not submission:
        _write_failure_reward(logs_dir, 0, "submission.json empty / unparseable")
        return 1

    try:
        answer_key = json.loads(answer_key_path.read_text())
    except json.JSONDecodeError as e:
        _write_failure_reward(logs_dir, len(submission), f"answer_key parse error: {e}")
        return 1

    # Persist the post-salvage submission for downstream debugging.
    (logs_dir / "submission.json").write_text(json.dumps(submission, indent=2))

    # Pull gold FINDINGS / IMPRESSION from /tests/target_report.txt that
    # the bootstrap compose service staged before main started. Missing
    # gold means the bootstrap step didn't fetch it — that's a verifier /
    # environment bug, not an agent failure. Write a structured reward
    # AND re-raise so Harbor's exception_stats surfaces it loudly
    # (otherwise a silent reward=0 would look like a normal "agent did
    # poorly" outcome).
    try:
        _bootstrap_gold(answer_key, answer_key_path, logs_dir)
    except MissingGoldError as e:
        reason = f"MissingGoldError: {e}"
        _write_failure_reward(logs_dir, len(submission), reason)
        # Re-raise as an exception so Harbor catches it in result.json's
        # exception_stats under "MissingGoldError".
        raise

    try:
        result = evaluate_submission_rows(submission, answer_key)
    except Exception as e:  # noqa: BLE001
        _write_failure_reward(logs_dir, len(submission), f"evaluator crashed: {type(e).__name__}: {e}")
        return 1

    # reward.json: flat scalars Harbor consumes. ``mean_sig_errors`` is
    # the diagnostic — average number of clinically-significant errors
    # the CheXprompt judge attributed to this trial (averaged across
    # successful judge runs, then across rows). Lower is better. Pass
    # rate stays binary; mean_sig_errors lets you compare how badly
    # different models fail when they fail.
    reward_payload = {
        "reward": float(result["reward"]),
        "n_tasks": int(result["n_tasks"]),
        "n_pass": int(result["n_pass"]),
        "pass_rate": float(result["pass_rate"]),
        "mean_sig_errors": float(result.get("mean_sig_errors", 0.0)),
    }
    (logs_dir / "reward.json").write_text(json.dumps(reward_payload))

    # metrics.json: same scalars + per-row diagnostics.
    (logs_dir / "metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
