"""MIMIC-CXR report generation task normalization helpers.

Loads metadata, selects patients with longitudinal studies, and builds
Harbor task payloads where the agent must generate a radiology report
for a target study given prior imaging history.

Data sources:
- Metadata: /mnt/hlsrad8455624441/datasets/MIMIC-CXR-V2-512-NIFTI/mimic-cxr-2.0.0-metadata.csv.gz
- Images (JPG): /mnt/hlsrad8455624441/reinforcement/ying/mimic-cxr-jpg-2.0.0/files/
- Reports (zip): /mnt/hlsrad8455624441/datasets/MIMIC-CXR-V2-512-NIFTI/mimic-cxr-reports.zip
"""

from __future__ import annotations

import csv
import gzip
import random
import zipfile
from pathlib import Path
from typing import Any


# Metadata CSV still lives with the NIfTI dataset
DEFAULT_META_ROOT = Path("/mnt/hlsrad8455624441/datasets/MIMIC-CXR-V2-512-NIFTI")

# JPG images
DEFAULT_IMAGE_ROOT = Path("/mnt/hlsrad8455624441/reinforcement/ying/mimic-cxr-jpg-2.0.0/files")

# Reports zip
DEFAULT_REPORTS_ZIP = Path(
    "/mnt/hlsrad8455624441/datasets/MIMIC-CXR-V2-512-NIFTI/mimic-cxr-reports.zip"
)


def load_split_assignments(meta_root: Path | None = None) -> dict[str, str]:
    """Load study_id → split (train/validate/test) from mimic-cxr-2.0.0-split.csv.gz.

    The split file has one row per DICOM; we take the split label of the first
    row seen for each study (rows for the same study share a label in MIMIC-CXR).
    """
    if meta_root is None:
        meta_root = DEFAULT_META_ROOT
    split_path = meta_root / "mimic-cxr-2.0.0-split.csv.gz"
    splits: dict[str, str] = {}
    with gzip.open(split_path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("study_id")
            if sid and sid not in splits:
                splits[sid] = row.get("split", "")
    return splits


def load_metadata(meta_root: Path | None = None) -> list[dict[str, Any]]:
    """Load MIMIC-CXR metadata CSV (one row per DICOM image).

    Returns list of dicts with keys: dicom_id, subject_id, study_id,
    PerformedProcedureStepDescription, ViewPosition, StudyDate, StudyTime, etc.
    """
    if meta_root is None:
        meta_root = DEFAULT_META_ROOT
    meta_path = meta_root / "mimic-cxr-2.0.0-metadata.csv.gz"
    rows: list[dict[str, Any]] = []
    with gzip.open(meta_path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _parse_study_datetime(date_str: str, time_str: str) -> str:
    """Convert StudyDate (YYYYMMDD) + StudyTime (HHMMSS.frac) to readable timestamp.

    DICOM StudyTime may omit leading zeros (e.g., '80556.875' for 08:05:56).
    We zero-pad the integer part to 6 digits before parsing.
    """
    if not date_str or len(date_str) < 8:
        return ""
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:8]

    # Split off fractional seconds and zero-pad integer part to HHMMSS
    parts = time_str.split(".")
    time_int = parts[0].zfill(6) if parts[0] else "000000"

    hours = time_int[0:2]
    minutes = time_int[2:4]
    seconds = time_int[4:6]

    return f"{year}-{month}-{day} {hours}:{minutes}:{seconds}"


def build_patient_studies(metadata_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group metadata by patient, then by study, sorted chronologically.

    Returns:
        {subject_id: [study_dict, ...]} where each study_dict has:
            study_id, study_datetime, procedure, views: [{dicom_id, view_position}]
    """
    # Group DICOMs by (subject_id, study_id)
    patient_studies: dict[str, dict[str, dict[str, Any]]] = {}
    for row in metadata_rows:
        subj = row["subject_id"]
        study = row["study_id"]

        if subj not in patient_studies:
            patient_studies[subj] = {}

        if study not in patient_studies[subj]:
            patient_studies[subj][study] = {
                "study_id": study,
                "subject_id": subj,
                "study_date": row.get("StudyDate", ""),
                "study_time": row.get("StudyTime", ""),
                "study_datetime": _parse_study_datetime(
                    row.get("StudyDate", ""), row.get("StudyTime", "")
                ),
                "procedure": row.get("PerformedProcedureStepDescription", ""),
                "views": [],
            }

        patient_studies[subj][study]["views"].append(
            {
                "dicom_id": row["dicom_id"],
                "view_position": row.get("ViewPosition", ""),
            }
        )

    # Convert to sorted lists per patient
    result: dict[str, list[dict[str, Any]]] = {}
    for subj, studies in patient_studies.items():
        sorted_studies = sorted(studies.values(), key=lambda s: s["study_date"] + s["study_time"])
        result[subj] = sorted_studies

    return result


def select_eligible_patients(
    patient_studies: dict[str, list[dict[str, Any]]],
    image_root: Path | None = None,
    reports_zip: Path | None = None,
    meta_root: Path | None = None,
    min_studies: int = 2,
    target_split: str = "test",
    require_nonempty_findings_impression: bool = True,
) -> list[str]:
    """Return subject IDs eligible to become a report-generation task.

    A patient is eligible iff:
      - they have at least `min_studies` studies (priors + target);
      - all JPG study image directories exist on disk;
      - all study reports are present in the reports zip;
      - the chronologically last (target) study is in `target_split`
        (default "test" — only sample from the official MIMIC-CXR test split);
      - the target report parses into non-empty FINDINGS *and* IMPRESSION
        sections (otherwise there's nothing meaningful to evaluate against).

    Args:
        patient_studies: Output of build_patient_studies.
        image_root: Root of JPG dataset (with p10/p11/... subdirs).
        reports_zip: Path to mimic-cxr-reports.zip.
        meta_root: Directory containing mimic-cxr-2.0.0-split.csv.gz.
        min_studies: Minimum number of studies required.
        target_split: Required split assignment for the target study.
        require_nonempty_findings_impression: Drop patients whose target report
            has empty FINDINGS or IMPRESSION sections.

    Returns:
        List of eligible subject_ids.
    """
    if image_root is None:
        image_root = DEFAULT_IMAGE_ROOT
    if reports_zip is None:
        reports_zip = DEFAULT_REPORTS_ZIP

    import time as _time
    import sys as _sys

    def _log(msg: str) -> None:
        print(f"  [eligibility] {msg}", flush=True)

    t = _time.time()
    splits = load_split_assignments(meta_root)
    _log(f"loaded split CSV in {_time.time()-t:.2f}s ({len(splits)} studies)")

    # Pass 1: in-memory filters (no disk I/O). Order matters — apply the
    # cheapest, most-restrictive checks first so we hit the network mount
    # the fewest times. The target-split filter alone shrinks 65K → ~few hundred.
    t = _time.time()
    pre_disk: list[str] = []
    for subj, studies in patient_studies.items():
        if len(studies) < min_studies:
            continue
        if splits.get(studies[-1]["study_id"]) != target_split:
            continue
        pre_disk.append(subj)
    _log(
        f"pass1 (in-memory split={target_split} + min_studies={min_studies}): "
        f"{_time.time()-t:.2f}s, {len(pre_disk)} candidates"
    )

    # Pass 2: disk + zip presence checks. The iterdir() call hits the network
    # mount (~0.7s per patient) so we parallelize across threads — the work
    # is IO-bound and threads scale almost linearly until the mount saturates.
    t = _time.time()
    with zipfile.ZipFile(reports_zip) as zf:
        t_zip = _time.time()
        zip_names = set(zf.namelist())
        _log(f"  zip namelist read in {_time.time()-t_zip:.2f}s ({len(zip_names)} entries)")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _check(subj: str) -> str | None:
            studies = patient_studies[subj]
            group = _patient_group(subj)
            patient_img_dir = image_root / group / f"p{subj}"
            try:
                existing = {p.name for p in patient_img_dir.iterdir() if p.is_dir()}
            except (FileNotFoundError, NotADirectoryError):
                return None
            if not all(f"s{s['study_id']}" in existing for s in studies):
                return None
            if not all(
                f"files/{group}/p{subj}/s{s['study_id']}.txt" in zip_names for s in studies
            ):
                return None
            return subj

        candidates: list[str] = []
        report_every = max(1, len(pre_disk) // 20)
        with ThreadPoolExecutor(max_workers=32) as pool:
            futures = {pool.submit(_check, subj): subj for subj in pre_disk}
            for done_count, fut in enumerate(as_completed(futures), start=1):
                result = fut.result()
                if result is not None:
                    candidates.append(result)
                if done_count % report_every == 0:
                    _log(
                        f"    pass2 progress: {done_count}/{len(pre_disk)} scanned, "
                        f"{len(candidates)} kept, {_time.time()-t:.1f}s elapsed"
                    )
        # ThreadPoolExecutor `as_completed` returns in completion order,
        # which varies across runs. Sort so downstream sampling is stable.
        candidates.sort()
        _log(
            f"pass2 (disk + zip presence, parallel): {_time.time()-t:.2f}s, "
            f"{len(candidates)} candidates remain"
        )

        if not require_nonempty_findings_impression:
            return candidates

        # Pass 3: target report must have CLEAR FINDINGS + IMPRESSION headers
        # (exactly one of each, in order, with non-trivial bodies).
        t = _time.time()
        eligible: list[str] = []
        for subj in candidates:
            target_sid = patient_studies[subj][-1]["study_id"]
            group = _patient_group(subj)
            arcname = f"files/{group}/p{subj}/s{target_sid}.txt"
            try:
                report_text = zf.read(arcname).decode("utf-8")
            except Exception:
                continue
            if has_clear_findings_impression(report_text):
                eligible.append(subj)
        _log(
            f"pass3 (target has clear FINDINGS+IMPRESSION headers): "
            f"{_time.time()-t:.2f}s, {len(eligible)} eligible"
        )
        return eligible


def sample_patients(
    eligible: list[str],
    sample_size: int = 50,
    seed: int = 42,
) -> list[str]:
    """Deterministically sample patients.

    Args:
        eligible: List of eligible subject_ids.
        sample_size: Number of patients to sample.
        seed: Random seed for reproducibility.

    Returns:
        List of sampled subject_ids.
    """
    rng = random.Random(seed)
    if len(eligible) <= sample_size:
        return list(eligible)
    return rng.sample(eligible, sample_size)


def _patient_group(subject_id: str) -> str:
    """Compute the top-level group directory name (e.g., 'p10' for subject 10000032)."""
    return f"p{subject_id[:2]}"


def read_report(
    subject_id: str,
    study_id: str,
    reports_zip: Path | None = None,
    zf: "zipfile.ZipFile | None" = None,
) -> str:
    """Read a report .txt from the mimic-cxr-reports.zip archive.

    If `zf` (an already-open ZipFile) is provided, it is reused — opening the
    zip on the network mount costs ~1s, so callers reading multiple reports
    for the same patient should pass an open handle.
    """
    group = _patient_group(subject_id)
    arcname = f"files/{group}/p{subject_id}/s{study_id}.txt"
    if zf is not None:
        return zf.read(arcname).decode("utf-8")
    if reports_zip is None:
        reports_zip = DEFAULT_REPORTS_ZIP
    with zipfile.ZipFile(reports_zip) as opened:
        return opened.read(arcname).decode("utf-8")


# Canonical MIMIC-CXR section names; order roughly matches typical reports.
REPORT_SECTIONS = (
    "EXAMINATION",
    "INDICATION",
    "HISTORY",
    "TECHNIQUE",
    "COMPARISON",
    "FINDINGS",
    "IMPRESSION",
    "RECOMMENDATION",
    "NOTIFICATION",
)

import re as _re

_SECTION_HEADER_RE = _re.compile(
    r"^[\s>]*(" + "|".join(REPORT_SECTIONS) + r")\s*:\s*",
    flags=_re.IGNORECASE | _re.MULTILINE,
)


def parse_report_sections(text: str) -> dict[str, str]:
    """Parse a MIMIC-CXR free-text report into named sections.

    Returns a dict {SECTION_NAME_UPPER: body_text}. Whitespace inside each
    section body is preserved but leading/trailing blank lines are trimmed.
    Sections that do not appear in the report are omitted.
    """
    matches = list(_SECTION_HEADER_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip("\n")
        sections[name] = body.strip()
    return sections


def split_target_report(
    full_report: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """Split a target study's report into (given_sections, target_sections).

    given_sections: everything EXCEPT FINDINGS and IMPRESSION (provided to the agent)
    target_sections: only FINDINGS and IMPRESSION (the agent must generate these)
    """
    parsed = parse_report_sections(full_report)
    target_keys = {"FINDINGS", "IMPRESSION"}
    given = {k: v for k, v in parsed.items() if k not in target_keys}
    target = {k: v for k, v in parsed.items() if k in target_keys}
    return given, target


def has_clear_findings_impression(text: str, min_body_chars: int = 5) -> bool:
    """Return True iff `text` contains a clean, unambiguous FINDINGS+IMPRESSION pair.

    A report passes iff:
      - exactly one FINDINGS section header (start-of-line, "FINDINGS:")
      - exactly one IMPRESSION section header (start-of-line, "IMPRESSION:")
      - FINDINGS appears before IMPRESSION
      - both bodies have at least `min_body_chars` non-whitespace characters

    This rules out reports where the words appear inline (not as headers),
    where they appear multiple times, or where the section is empty / a stub.
    """
    matches = list(_SECTION_HEADER_RE.finditer(text))
    findings_positions = [m.start() for m in matches if m.group(1).upper() == "FINDINGS"]
    impression_positions = [m.start() for m in matches if m.group(1).upper() == "IMPRESSION"]

    if len(findings_positions) != 1 or len(impression_positions) != 1:
        return False
    if findings_positions[0] >= impression_positions[0]:
        return False

    sections = parse_report_sections(text)
    findings_body = sections.get("FINDINGS", "").strip()
    impression_body = sections.get("IMPRESSION", "").strip()
    if len(findings_body) < min_body_chars or len(impression_body) < min_body_chars:
        return False
    return True


def build_task_for_patient(
    subject_id: str,
    studies: list[dict[str, Any]],
    reports_zip: Path | None = None,
    zf: "zipfile.ZipFile | None" = None,
) -> dict[str, Any]:
    """Build a single Harbor task dict for a patient.

    The target study is the chronologically last study. The agent receives
    all prior studies (images + reports) and the target study's images,
    but must generate the target study's report.

    If `zf` (an already-open ZipFile of the reports archive) is provided, it
    is reused for every report read — opening the zip on the network mount
    is ~1s, so passing one open handle is much faster than re-opening per study.

    Returns:
        Task dict with keys: task_id, subject_id, target_study, history,
        instruction, final_answer, payload.
    """
    target = studies[-1]
    history = studies[:-1]

    # Build image paths (container paths under /data/patient/<timestamp>_s<study>/).
    def _folder_name(study: dict[str, Any]) -> str:
        safe = study["study_datetime"].replace(" ", "_").replace(":", "-")
        return f"{safe}_s{study['study_id']}"

    def _image_paths(study: dict[str, Any]) -> list[dict[str, str]]:
        folder = _folder_name(study)
        return [
            {
                "dicom_id": v["dicom_id"],
                "view_position": v["view_position"],
                "path": f"/data/patient/{folder}/{v['dicom_id']}.jpg",
            }
            for v in study["views"]
        ]

    # Build history entries — reports are referenced by path only.
    # The agent must `cat` them from /data/patient/<folder>/report.txt.
    history_entries = []
    for s in history:
        folder = _folder_name(s)
        history_entries.append(
            {
                "study_id": s["study_id"],
                "study_datetime": s["study_datetime"],
                "procedure": s["procedure"],
                "views": _image_paths(s),
                "report_path": f"/data/patient/{folder}/report.txt",
            }
        )

    # Split target report: agent SEES given_sections, must GENERATE findings+impression
    target_full = read_report(subject_id, target["study_id"], reports_zip, zf=zf)
    given_sections, _target_sections = split_target_report(target_full)

    task_id = f"mimic_cxr_report_{subject_id}_{target['study_id']}"

    return {
        "task_id": task_id,
        "subject_id": subject_id,
        "target_study": {
            "study_id": target["study_id"],
            "study_datetime": target["study_datetime"],
            "procedure": target["procedure"],
            "views": _image_paths(target),
            "given_sections": given_sections,
        },
        "history": history_entries,
        "instruction": _build_instruction(subject_id, target, history_entries, given_sections),
        "final_answer": "",
        "payload": None,
    }


def _format_given_sections(sections: dict[str, str]) -> str:
    """Render given sections in canonical order as plain text for instructions."""
    lines = []
    for name in REPORT_SECTIONS:
        if name in {"FINDINGS", "IMPRESSION"}:
            continue
        if name in sections and sections[name]:
            lines.append(f"{name}: {sections[name]}")
            lines.append("")
    return "\n".join(lines).rstrip()


def _format_target_sections(sections: dict[str, str]) -> str:
    """Render the FINDINGS and IMPRESSION ground truth as a single answer string.

    Format matches what the agent is told to produce:
        FINDINGS:
        <text>

        IMPRESSION:
        <text>
    """
    parts = []
    for name in ("FINDINGS", "IMPRESSION"):
        body = sections.get(name, "").strip()
        if body:
            parts.append(f"{name}:\n{body}")
    return "\n\n".join(parts)


def _build_instruction(
    subject_id: str,
    target: dict[str, Any],
    history: list[dict[str, Any]],
    given_sections: dict[str, str],
) -> str:
    """Build the agent-facing instruction for report generation."""
    lines = [
        "Generate the FINDINGS and IMPRESSION sections of a radiology report",
        "for the target chest X-ray study.",
        "",
        f"Patient ID: {subject_id}",
        f"Target Study ID: {target['study_id']}",
        f"Target Study Date: {target['study_datetime']}",
        f"Target Procedure: {target['procedure']}",
        f"Target Views: {', '.join(v['view_position'] for v in target['views'])}",
        "",
    ]

    if history:
        lines.append(
            f"This patient has {len(history)} prior study/studies available for reference."
        )
        lines.append("Prior reports and images are provided in the task data.")
        lines.append("")

    given_text = _format_given_sections(given_sections)
    if given_text:
        lines.extend(
            [
                "## Provided sections of the target report",
                "",
                "These sections of the target study's report are GIVEN to you. Use them",
                "as context but do NOT include them in your output.",
                "",
                given_text,
                "",
            ]
        )

    lines.extend(
        [
            "## Your output",
            "",
            "Produce only the FINDINGS and IMPRESSION sections, formatted exactly as:",
            "",
            "FINDINGS:",
            "<your findings text>",
            "",
            "IMPRESSION:",
            "<your impression text>",
            "",
            "Use the target study's images, the provided sections above, and the patient's",
            "prior imaging history to write accurate, clinically appropriate findings and",
            "an impression. Do not repeat the EXAMINATION/INDICATION/TECHNIQUE/COMPARISON/HISTORY sections.",
        ]
    )

    return "\n".join(lines)


def build_answer_key_for_patient(
    subject_id: str,
    studies: list[dict[str, Any]],
    reports_zip: Path | None = None,
    zf: "zipfile.ZipFile | None" = None,
) -> dict[str, Any]:
    """Build the answer key entry for a patient task.

    The expected answer is FINDINGS + IMPRESSION of the target study report.
    Pass `zf` (an already-open ZipFile) to avoid re-opening the reports
    archive — this is significantly faster on a network mount.
    """
    target = studies[-1]
    task_id = f"mimic_cxr_report_{subject_id}_{target['study_id']}"
    ground_truth_report = read_report(subject_id, target["study_id"], reports_zip, zf=zf)
    _given, target_sections = split_target_report(ground_truth_report)
    expected_answer = _format_target_sections(target_sections)

    return {
        "task_id": task_id,
        "category": "report_generation",
        "difficulty": "hard",
        "expected_answer": expected_answer,
        "expected_findings": target_sections.get("FINDINGS", ""),
        "expected_impression": target_sections.get("IMPRESSION", ""),
        "full_ground_truth_report": ground_truth_report,
        "subject_id": subject_id,
        "target_study_id": target["study_id"],
        "num_prior_studies": len(studies) - 1,
    }
