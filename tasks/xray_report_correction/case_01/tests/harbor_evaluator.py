"""CheXprompt-based evaluator for MIMIC-CXR report generation.

The agent submits a FINDINGS + IMPRESSION radiology report into
``final_answer``. This evaluator:

  1. extracts the candidate FINDINGS section (ignoring IMPRESSION, which
     is not scored under CheXprompt's contract);
  2. reads the gold FINDINGS directly from ``tests/task_answer_key.json``
     (``expected_findings``), which the host generator pre-extracted from
     the credentialed MIMIC reports zip at task-generation time;
  3. calls CheXprompt (https://github.com/microsoft/chexprompt) via
     OpenAI / Azure OpenAI to count clinical errors across 6 categories ×
     2 severity tiers;
  4. emits ``reward = 1.0`` iff
     ``sum(clinically_significant.values()) == 0``, else ``0.0``.
     Per-category counts are persisted to ``metrics.json`` for analysis.

The pass bar is "no clinically significant error" because CheXprompt's
own paper separates clinically significant errors (would change
management) from insignificant ones (phrasing differences, redundant
omissions). The first is the clinically meaningful boundary.

Runtime requirements (failing any of these returns ``reward=0.0`` with a
structured error string in the result row, so a failed verifier never
masquerades as a passing agent):

  * OpenAI env vars exported before the verifier runs:
    ``OPENAI_API_KEY`` and either ``OPENAI_BASE_URL`` (vanilla OpenAI) or
    ``OPENAI_API_BASE`` + ``OPENAI_API_VERSION`` (Azure).
    ``CHEXPROMPT_DEPLOYMENT`` selects the model / deployment name
    (e.g. ``gpt-4-1106-preview`` or whichever Azure deployment is in use).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


# Header detector for FINDINGS / IMPRESSION (case-insensitive, any spacing
# around the colon).
_SECTION_RE = re.compile(r"\b(findings|impression)\s*:\s*", flags=re.IGNORECASE)


def _extract_findings(text: str) -> str:
    """Return just the FINDINGS section of ``text``.

    Behavior:
      * No headers at all → whole text treated as findings.
      * FINDINGS header present → return body up to next header / EOF.
      * Only IMPRESSION header present → return text BEFORE the
        IMPRESSION header (best guess that the agent put findings first
        without a header).
    """
    if not text:
        return ""
    text = text.strip()
    # Drop optional "FINAL REPORT" boilerplate.
    text = re.sub(r"^\s*final report\s*", "", text, flags=re.IGNORECASE)
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return text
    for i, m in enumerate(matches):
        if m.group(1).lower() == "findings":
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[start:end].strip()
    # FINDINGS header missing but IMPRESSION present.
    first_impression = matches[0]
    pre = text[: first_impression.start()].strip()
    return pre or text.strip()


def _configure_openai_for_chexprompt() -> str | None:
    """Configure the legacy openai==0.28 SDK for either vanilla OpenAI or
    Azure OpenAI based on env vars. Returns an error string if config is
    invalid, None otherwise. Must be called before importing CheXprompt.

    Accepts both naming conventions:

    * Azure-canonical (preferred when set):
        ``AZURE_OPENAI_API_KEY`` / ``AZURE_OPENAI_ENDPOINT`` /
        ``AZURE_OPENAI_API_VERSION``  (deployment via
        ``AZURE_OPENAI_DEPLOYMENT`` or ``CHEXPROMPT_DEPLOYMENT``).
    * Legacy openai-SDK names (works for both vanilla and Azure):
        ``OPENAI_API_KEY`` / ``OPENAI_API_BASE`` / ``OPENAI_API_VERSION``.
    * Vanilla OpenAI: ``OPENAI_API_KEY`` (+ optional ``OPENAI_BASE_URL``).

    Detection order: AZURE_OPENAI_* (if endpoint set) → OPENAI_API_BASE
    + OPENAI_API_VERSION (Azure-shaped) → vanilla OpenAI.
    """
    import openai  # noqa: PLC0415 — defer until we have env

    # Azure-canonical naming has priority when both endpoint and key are set.
    # Endpoint accepts three aliases: ``AZURE_OPENAI_ENDPOINT`` (canonical),
    # ``AZURE_OPENAI_BASE_URL`` (sometimes used), or ``OPENAI_API_BASE``
    # (legacy openai-SDK).
    azure_endpoint = (
        os.environ.get("AZURE_OPENAI_ENDPOINT")
        or os.environ.get("AZURE_OPENAI_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
    )
    azure_version = os.environ.get("AZURE_OPENAI_API_VERSION") or os.environ.get("OPENAI_API_VERSION")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")

    if azure_endpoint and azure_version and azure_key:
        openai.api_type = "azure"
        openai.api_base = azure_endpoint
        openai.api_version = azure_version
        openai.api_key = azure_key
        return None

    # Fall through to vanilla OpenAI.
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return (
            "No API key found — set either AZURE_OPENAI_API_KEY "
            "(+ AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_VERSION) for Azure, "
            "or OPENAI_API_KEY for vanilla OpenAI."
        )
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    for suffix in ("/chat/completions", "/completions"):
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)]
    openai.api_type = "open_ai"
    openai.api_base = base_url
    openai.api_key = api_key
    return None


def _call_chexprompt(reference: str, candidate: str) -> dict[str, Any]:
    """Call CheXprompt's ``ReportEvaluator`` against the configured
    OpenAI / Azure deployment.

    Returns either the CheXprompt count dict
        {
          "clinically_significant":   {"A": n, ..., "F": n},
          "clinically_insignificant": {"A": n, ..., "F": n},
        }
    or ``{"error": "<reason>"}``. An error here counts as verifier
    failure (reward 0, but the agent did not "pass").
    """
    try:
        import chexprompt  # noqa: F401, PLC0415
    except ImportError as e:
        return {"error": f"chexprompt not installed: {e}"}

    # Default to gpt-5.4 — it's stricter than gpt-4o at counting clinical
    # errors in radiology FINDINGS, which matches the "no clinically
    # significant error = pass" bar. Override via CHEXPROMPT_DEPLOYMENT
    # (or AZURE_OPENAI_DEPLOYMENT — same meaning, whichever .env carries).
    deployment = (
        os.environ.get("CHEXPROMPT_DEPLOYMENT")
        or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        or "gpt-5.4"
    )

    cfg_err = _configure_openai_for_chexprompt()
    if cfg_err:
        return {"error": cfg_err}

    import openai  # noqa: PLC0415
    from chexprompt.evaluator import ReportEvaluator  # noqa: PLC0415

    # CheXprompt's ``generate_openai_chat_completion`` hardcodes
    # ``engine=`` (Azure-only) and passes ``max_tokens`` + ``temperature``
    # + ``top_p`` + the two penalties. We patch that method to:
    #
    #   1. switch to ``model=`` when running against vanilla OpenAI
    #      (openai==0.28 routes Azure on ``engine=`` and vanilla on
    #      ``model=``),
    #   2. swap ``max_tokens`` → ``max_completion_tokens`` and drop
    #      ``temperature`` / ``top_p`` / penalties for gpt-5.x reasoning
    #      models (they reject all those params).
    #
    # Both branches reuse CheXprompt's prompt template, parser, and
    # retry loop unchanged.
    is_gpt5 = deployment.startswith("gpt-5")
    is_azure = openai.api_type == "azure"

    def _patched_chat(self, formatted_prompt):
        kwargs: dict[str, Any] = {
            "messages": formatted_prompt,
            "stop": self.stop,
        }
        if is_azure:
            kwargs["engine"] = self.engine
        else:
            kwargs["model"] = self.engine
        if is_gpt5:
            kwargs["max_completion_tokens"] = self.max_tokens
            # gpt-5.x rejects temperature / top_p / penalties.
        else:
            kwargs["max_tokens"] = self.max_tokens
            kwargs["temperature"] = self.temperature
            kwargs["top_p"] = self.top_p
            kwargs["frequency_penalty"] = self.frequency_penalty
            kwargs["presence_penalty"] = self.presence_penalty
        return openai.ChatCompletion.create(**kwargs)

    ReportEvaluator.generate_openai_chat_completion = _patched_chat

    # gpt-5.x reasoning models burn many tokens on internal thinking before
    # emitting the answer. CheXprompt's 128-token default clips the
    # response; bump to 2048 so the parser still sees the full tuple list.
    evaluator = ReportEvaluator(
        engine=deployment,
        max_retries=2,
        max_tokens=(2048 if is_gpt5 else 128),
    )
    try:
        result = evaluator.evaluate(reference, candidate)
    except Exception as e:  # noqa: BLE001
        return {"error": f"CheXprompt call failed: {type(e).__name__}: {e}"}
    if isinstance(result, list):
        if not result:
            return {"error": "CheXprompt returned empty list"}
        result = result[0]
    if not isinstance(result, dict) or "clinically_significant" not in result:
        return {"error": f"CheXprompt returned unexpected shape: {result!r}"}
    return result


def evaluate_submission_rows(
    submission: list[dict[str, Any]],
    answer_key: list[dict[str, Any]],
) -> dict[str, Any]:
    """Score the agent's submission against the verifier-only answer key.

    Args:
        submission: list of ``{task_id, instruction, final_answer, ...}``
            rows from ``/workspace/submission.json``.
        answer_key: list of verifier-only rows. Each row must carry
            ``task_id`` and ``expected_findings`` (the gold FINDINGS
            section). ``expected_impression`` is allowed but ignored —
            CheXprompt scores FINDINGS only.

    Returns:
        Aggregate dict ``{reward, n_tasks, n_pass, pass_rate, results}``.
        ``reward`` is binary at the trial level (1.0 iff every row
        passed). For the curated 1-row-per-trial layout, this equals
        ``pass_rate``.
    """
    key_by_id = {k["task_id"]: k for k in answer_key}

    results: list[dict[str, Any]] = []
    n_pass = 0
    for sub in submission:
        task_id = sub.get("task_id", "")
        key = key_by_id.get(task_id, {})
        study_id = str(key.get("study_id", ""))
        gold_findings = str(key.get("expected_findings", "")).strip()
        candidate_findings = _extract_findings(str(sub.get("final_answer", "")))

        row: dict[str, Any] = {
            "task_id": task_id,
            "study_id": study_id,
            "candidate_findings_len": len(candidate_findings),
            "gold_findings_len": len(gold_findings),
        }

        if not candidate_findings:
            row.update({"match": False, "error": "empty candidate findings"})
            results.append(row)
            continue
        if not gold_findings:
            row.update({"match": False, "error": f"gold findings missing for study_id={study_id}"})
            results.append(row)
            continue

        # 5-of-5 vote: call CheXprompt 5 times; pass iff at least 3 runs
        # return zero clinically-significant errors. The threshold is
        # ABSOLUTE — not "majority of successful runs" — so partial
        # rate-limit failures (which would lower the denominator under a
        # dynamic majority rule) cannot mask a fail as a pass. If fewer
        # than 3 runs succeed, the row fails with the last-seen error.
        #
        # CheXprompt's gpt-5.x judge is non-deterministic (no
        # temperature / top_p control under that model family) and we've
        # observed it miss subtle severity downgrades on single calls.
        # 3-of-5 voting damps that noise more than 2-of-3 did.
        n_votes = int(os.environ.get("CHEXPROMPT_VOTES", "5"))
        threshold = int(os.environ.get("CHEXPROMPT_PASS_THRESHOLD", "3"))
        vote_runs: list[dict[str, Any]] = []
        sig_zero_votes = 0
        any_error: str | None = None
        for i in range(n_votes):
            chex = _call_chexprompt(reference=gold_findings, candidate=candidate_findings)
            if "error" in chex:
                any_error = chex["error"]
                vote_runs.append({"run": i + 1, "error": chex["error"]})
                continue
            sig = chex.get("clinically_significant", {})
            insig = chex.get("clinically_insignificant", {})
            sig_total = sum(int(v) for v in sig.values())
            insig_total = sum(int(v) for v in insig.values())
            vote_runs.append({
                "run": i + 1,
                "clinically_significant": sig,
                "clinically_insignificant": insig,
                "n_sig_errors": sig_total,
                "n_insig_errors": insig_total,
            })
            if sig_total == 0:
                sig_zero_votes += 1

        ok_runs = [r for r in vote_runs if "error" not in r]
        if not ok_runs:
            row.update({"match": False, "error": any_error or "all CheXprompt runs failed"})
            results.append(row)
            continue
        match = sig_zero_votes >= threshold
        # Diagnostic metric: average number of clinically-significant
        # errors across the successful CheXprompt runs for this row.
        # Reported in addition to pass/fail so we can see *how badly*
        # the candidate fails (1 sig error vs. 5) and compare models on
        # severity rather than just binary pass rate.
        run_sig_totals = [r["n_sig_errors"] for r in ok_runs]
        mean_sig = sum(run_sig_totals) / len(run_sig_totals) if run_sig_totals else 0.0
        row.update({
            "match": match,
            "votes_total": len(ok_runs),
            "votes_sig_zero": sig_zero_votes,
            "votes_threshold": threshold,
            "mean_sig_errors": mean_sig,
            "runs": vote_runs,
        })
        if match:
            n_pass += 1
        results.append(row)

    n_tasks = len(submission)
    pass_rate = n_pass / n_tasks if n_tasks else 0.0
    reward = 1.0 if n_tasks > 0 and n_pass == n_tasks else 0.0
    # Trial-level average clinically-significant error count, averaged
    # across rows that have a usable mean (i.e. rows where at least one
    # CheXprompt run succeeded). Rows with empty/failed submissions are
    # *intentionally excluded* — they didn't actually score 0 errors, they
    # didn't score at all. Including them as 0.0 would silently reward a
    # model that refuses to write anything. When no row scored, return
    # None so the caller drops the key from reward.json (and so any
    # downstream aggregate skips this trial via "is not None" guards
    # instead of biasing the mean toward 0). Pass rate still penalizes
    # the empty submission via ``match=False`` above.
    row_means = [r["mean_sig_errors"] for r in results if "mean_sig_errors" in r]
    trial_mean_sig = sum(row_means) / len(row_means) if row_means else None
    return {
        "reward": reward,
        "n_tasks": n_tasks,
        "n_pass": n_pass,
        "pass_rate": pass_rate,
        "mean_sig_errors": trial_mean_sig,
        "results": results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MIMIC-CXR CheXprompt verifier")
    parser.add_argument("--submission", required=True)
    parser.add_argument("--answer-key", required=True)
    args = parser.parse_args()
    sub = json.loads(Path(args.submission).read_text())
    key = json.loads(Path(args.answer_key).read_text())
    print(json.dumps(evaluate_submission_rows(sub, key), indent=2))
