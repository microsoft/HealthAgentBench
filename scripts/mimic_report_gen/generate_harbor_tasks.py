#!/usr/bin/env python3
"""Generate Harbor tasks for MIMIC-CXR report generation benchmark.

Each task is one patient. The agent sees:
  - All prior studies: JPG images + reports + timestamps
  - Target study: JPG images + timestamps (NO report)
The agent must generate the target study's radiology report.

Data sources:
  - Metadata: /mnt/hlsrad8455624441/datasets/MIMIC-CXR-V2-512-NIFTI/mimic-cxr-2.0.0-metadata.csv.gz
  - Images (JPG): /mnt/hlsrad8455624441/reinforcement/ying/mimic-cxr-jpg-2.0.0/files/
  - Reports (zip): /mnt/hlsrad8455624441/datasets/MIMIC-CXR-V2-512-NIFTI/mimic-cxr-reports.zip

At generation time, prior reports are extracted from the zip and baked into the
task workspace at environment/workspace/reports/s<study>.txt. Only JPG image
directories are mounted from the host. The target study's report is never
extracted or mounted; it lives only in tests/task_answer_key.json.

Usage (default: every eligible patient, latest study as target):
    python scripts/mimic_report_gen/generate_harbor_tasks.py \
      --output-root tasks/mimic_report_gen

Usage (custom sample size):
    python scripts/mimic_report_gen/generate_harbor_tasks.py \
      --output-root tasks/mimic_report_gen \
      --sample-size 100
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from normalization import (
    DEFAULT_IMAGE_ROOT,
    DEFAULT_META_ROOT,
    DEFAULT_REPORTS_ZIP,
    build_answer_key_for_patient,
    build_patient_studies,
    build_task_for_patient,
    load_metadata,
    sample_patients,
    select_eligible_patients,
)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2))


def _generate_task_toml(task_id: str, subject_id: str) -> str:
    return f"""version = "1.0"

[metadata]
benchmark = "mimic_cxr_report_generation"
mode = "single-task"
description = "Generate radiology report for patient {subject_id}"
task_id = "{task_id}"
submission_path = "/workspace/submission.json"

[verifier]
timeout_sec = 900.0

[agent]
timeout_sec = 3600.0

[environment]
# First cold build downloads ~500 MB CheXbert weights + installs torch, so
# give ourselves plenty of headroom. Cached rebuilds are much faster.
build_timeout_sec = 1800.0
allow_internet = true
cpus = 2
memory_mb = 4096
storage_mb = 10240
gpus = 0
mcp_servers = []
"""


def _generate_instruction_md(task: dict[str, Any]) -> str:
    target = task["target_study"]
    history = task["history"]
    n_prior = len(history)

    lines = [
        "# Radiology Report — Findings & Impression Generation",
        "",
        "You are working inside a task environment that contains:",
        "",
        f"- Chest X-ray images for patient `{task['subject_id']}`",
        f"- {n_prior} prior study/studies with full reports and images under `/data/patient/`",
        f"- Target study images (study `{target['study_id']}`) — you must generate FINDINGS and IMPRESSION for this study",
        "- Task data at `/workspace/benchmark_tasks.json`",
        "- Editable submission at `/workspace/submission.json`",
        "",
        "The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,",
        "COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under",
        "`target_study.given_sections` and in the instruction text. You must NOT regenerate them.",
        "",
        "Your final work product is `/workspace/submission.json`.",
        "",
        "## Patient History",
        "",
    ]

    if history:
        for i, h in enumerate(history, 1):
            folder = _timestamp_folder_name(h["study_datetime"], h["study_id"])
            lines.append(f"### Prior Study {i}: {h['study_id']}")
            lines.append(f"- **Date:** {h['study_datetime']}")
            lines.append(f"- **Procedure:** {h['procedure']}")
            views_str = ", ".join(v["view_position"] for v in h["views"])
            lines.append(f"- **Views:** {views_str}")
            lines.append(f"- **Folder:** `/data/patient/{folder}/`")
            lines.append(f"- **Report:** `/data/patient/{folder}/report.txt`")
            img_paths = [v["path"] for v in h["views"]]
            lines.append(f"- **Images:** {', '.join(f'`{p}`' for p in img_paths)}")
            lines.append("")
    else:
        lines.append("No prior studies available for this patient.")
        lines.append("")

    target_folder = _timestamp_folder_name(target["study_datetime"], target["study_id"])
    lines.extend(
        [
            "## Target Study",
            "",
            f"- **Study ID:** {target['study_id']}",
            f"- **Date:** {target['study_datetime']}",
            f"- **Procedure:** {target['procedure']}",
            f"- **Views:** {', '.join(v['view_position'] for v in target['views'])}",
            f"- **Folder:** `/data/patient/{target_folder}/` (contains only `.jpg` images — no `report.txt`)",
        ]
    )
    img_paths = [v["path"] for v in target["views"]]
    lines.append(f"- **Images:** {', '.join(f'`{p}`' for p in img_paths)}")

    # Provided sections of the target report
    given = target.get("given_sections") or {}
    if given:
        lines.append("")
        lines.append("### Provided sections of the target report")
        lines.append("")
        lines.append(
            "These are GIVEN to you. Use them as context but do NOT include them in your output."
        )
        lines.append("")
        for name in (
            "EXAMINATION",
            "INDICATION",
            "HISTORY",
            "TECHNIQUE",
            "COMPARISON",
        ):
            body = given.get(name, "").strip()
            if body:
                lines.append(f"**{name}:** {body}")
                lines.append("")

    lines.extend(
        [
            "## Your Task",
            "",
            "Produce ONLY the FINDINGS and IMPRESSION sections of the target study's report.",
            "Use the target study's images, the provided sections above, and the patient's",
            "prior imaging history (reports + images in `/data/patient/`) as context.",
            "",
            "Format your `final_answer` exactly as:",
            "",
            "```",
            "FINDINGS:",
            "<your findings text>",
            "",
            "IMPRESSION:",
            "<your impression text>",
            "```",
            "",
            "Do NOT include EXAMINATION/INDICATION/TECHNIQUE/COMPARISON/HISTORY headers in",
            "your answer — they are already part of the report and will be combined externally.",
            "",
            "## Submission Rules",
            "",
            "- Set `final_answer` to FINDINGS + IMPRESSION text only (free text)",
            "- Do NOT modify `task_id` or `instruction` fields",
            "- Work autonomously until the submission is complete",
            "",
            "**IMPORTANT: update `submission.json` using a JSON-aware tool (e.g., `python -c \"import json; ...\"`),",
            "NOT by editing the raw text. Manual string edits easily corrupt the JSON.**",
        ]
    )
    return "\n".join(lines)


def _generate_dockerfile() -> str:
    return """FROM python:3.12-slim

# Pre-install packages Harbor bootstraps for the agent runtime, plus bash/jq.
# wget + util-linux (flock) are used by entrypoint.sh to bootstrap missing
# MIMIC-CXR assets from PhysioNet on first run of any task container.
RUN apt-get update && apt-get install -y --no-install-recommends \\
    bash \\
    curl \\
    wget \\
    util-linux \\
    jq \\
    ripgrep \\
    && rm -rf /var/lib/apt/lists/*

# CheXbert dependencies for per-trial pathology labeling inside
# verify_meta_task.py. Pinned to versions compatible with f1chexbert:
#   - transformers<5: BertTokenizer.encode_plus was removed in 5.x
#   - scikit-learn: any 1.x is fine (we only call stable APIs)
# The CheXbert BERT weights (~440 MB) are pre-fetched at build time so task
# containers don't hit HuggingFace on every cold start.
RUN pip install --no-cache-dir \\
    'torch==2.4.1' \\
    'transformers<5' \\
    'scikit-learn>=1.3,<1.8' \\
    'f1chexbert' \\
    'huggingface_hub' \\
    'appdirs'
RUN python -c "\\
from huggingface_hub import hf_hub_download; \\
from appdirs import user_cache_dir; \\
import os, shutil; \\
cache = user_cache_dir('chexbert'); os.makedirs(cache, exist_ok=True); \\
src = hf_hub_download(repo_id='StanfordAIMI/RRG_scorers', filename='chexbert.pth', cache_dir=cache); \\
dst = os.path.join(cache, 'chexbert.pth'); \\
(os.symlink(src, dst) if not os.path.exists(dst) else None)"

WORKDIR /workspace

COPY environment/workspace/ /workspace/

# Manifest + entrypoint that materialize /data/patient/ at runtime
COPY environment/task_manifest.json /opt/task_manifest.json
COPY environment/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /logs/verifier /data/patient

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
"""


def _timestamp_folder_name(study_datetime: str, study_id: str) -> str:
    """Produce a filesystem-safe folder name like '2180-05-06_21-30-14_s50414267'."""
    safe = study_datetime.replace(" ", "_").replace(":", "-")
    return f"{safe}_s{study_id}"


def _build_task_manifest(task: dict[str, Any]) -> dict[str, Any]:
    """Build the manifest consumed by the entrypoint at container startup.

    It lists every study (chronologically) with folder name, whether it is the
    target, and DICOM ids / view positions. The entrypoint uses it to
    materialize /data/patient/<folder>/ by symlinking JPGs from the read-only
    mount and extracting non-target reports from the reports zip.
    """
    subject_id = task["subject_id"]
    target_study_id = task["target_study"]["study_id"]
    all_studies = task["history"] + [task["target_study"]]
    return {
        "subject_id": subject_id,
        "target_study_id": target_study_id,
        "studies": [
            {
                "folder": _timestamp_folder_name(s["study_datetime"], s["study_id"]),
                "study_id": s["study_id"],
                "study_datetime": s["study_datetime"],
                "procedure": s["procedure"],
                "is_target": s["study_id"] == target_study_id,
                "views": [
                    {"dicom_id": v["dicom_id"], "view_position": v["view_position"]}
                    for v in s["views"]
                ],
            }
            for s in all_studies
        ],
    }


def _generate_entrypoint() -> str:
    """Generate the entrypoint script that builds /data/patient/ at runtime.

    Reads /opt/task_manifest.json, symlinks JPGs from the read-only image mount
    into timestamped folders under /data/patient/, and extracts each prior
    study's report from the read-only reports zip. The target study's report
    is NEVER extracted.
    """
    return r"""#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Bootstrap any missing MIMIC-CXR assets for this task from PhysioNet.
#
# Mounts:
#   /data/_src/jpg_root          → mimic-cxr-jpg/2.1.0 dataset root (rw, shared)
#   /data/_src/patient_reports   → per-patient extracted prior-study .txt
#                                  files (rw, host-populated at generation
#                                  time). Contains ONLY this patient's
#                                  NON-TARGET reports.
#
# If patient_reports is empty (generation's host-side extraction was skipped),
# the entrypoint downloads the full reports zip into /tmp, extracts ONLY this
# patient's prior-study .txt files into the mount, then removes the /tmp zip
# so the agent can never read the target report.
# ---------------------------------------------------------------------------
MANIFEST=/opt/task_manifest.json
JPG_ROOT=/data/_src/jpg_root
PATIENT_REPORTS=/data/_src/patient_reports
SRC_IMAGES="$JPG_ROOT/files"
DEST=/data/patient

PN_BASE_REPORTS="https://physionet.org/files/mimic-cxr/2.1.0"
PN_BASE_JPG="https://physionet.org/files/mimic-cxr-jpg/2.1.0"

mkdir -p "$DEST" "$PATIENT_REPORTS"

bootstrap_assets() {
  # Per-patient lock: concurrent task containers for DIFFERENT patients
  # bootstrap in parallel (disjoint file subtrees), while tasks for the
  # SAME patient still serialize (guards against self-races).
  local subject_id
  subject_id="$(python3 -c 'import json; print(json.load(open("/opt/task_manifest.json"))["subject_id"])')"
  local lock_dir="$JPG_ROOT/.bootstrap.locks"
  local lock_file="$lock_dir/p${subject_id}.lock"
  mkdir -p "$JPG_ROOT" "$lock_dir"
  exec 9>"$lock_file"
  flock 9

  # --- Patient-specific prior reports ---
  # If any prior-study .txt is missing from the mount, fetch it directly
  # from PhysioNet's file tree (one small HTTP GET per missing study).
  # The target study's .txt is NEVER fetched, so it can't leak.
  if [ -n "${PN_USER:-}" ] && [ -n "${PN_PASS:-}" ]; then
    python3 - <<'PY' > /tmp/_missing_reports.txt
import json
from pathlib import Path

m = json.loads(Path("/opt/task_manifest.json").read_text())
subj = m["subject_id"]
group = f"p{subj[:2]}"
dest = Path("/data/_src/patient_reports")
for study in m["studies"]:
    if study["is_target"]:
        continue
    sid = study["study_id"]
    if not (dest / f"s{sid}.txt").exists():
        # PhysioNet URL-relative path (resolved via --base)
        print(f"files/{group}/p{subj}/s{sid}.txt")
PY
    if [ -s /tmp/_missing_reports.txt ]; then
      echo "[bootstrap] Fetching $(wc -l </tmp/_missing_reports.txt) missing prior report(s)..."
      (
        # Without -r, wget writes each URL to its basename in cwd → each
        # file lands at $PATIENT_REPORTS/s<sid>.txt directly.
        cd "$PATIENT_REPORTS"
        wget -c -N \
          --user "$PN_USER" --password "$PN_PASS" \
          -i /tmp/_missing_reports.txt \
          --base="$PN_BASE_REPORTS/"
      )
    fi
    rm -f /tmp/_missing_reports.txt
  elif ! ls "$PATIENT_REPORTS"/s*.txt >/dev/null 2>&1; then
    echo "[bootstrap] patient_reports empty and PN_USER/PN_PASS not set — agent will see no prior reports."
  fi

  # --- Per-study JPGs listed in the manifest ---
  if [ -z "${PN_USER:-}" ] || [ -z "${PN_PASS:-}" ]; then
    echo "[bootstrap] PN_USER/PN_PASS not set; skipping JPG download."
    return 0
  fi

  python3 - <<'PY' > /tmp/_missing_jpgs.txt
import json, os
from pathlib import Path

m = json.loads(Path("/opt/task_manifest.json").read_text())
subject_id = m["subject_id"]
group = f"p{subject_id[:2]}"
root = Path("/data/_src/jpg_root/files") / group / f"p{subject_id}"
missing = []
for study in m["studies"]:
    sdir = root / f"s{study['study_id']}"
    for v in study["views"]:
        jpg = sdir / f"{v['dicom_id']}.jpg"
        if not jpg.exists():
            # Path that wget -nH --cut-dirs=1 expects: relative to jpg_root
            rel = f"files/{group}/p{subject_id}/s{study['study_id']}/{v['dicom_id']}.jpg"
            missing.append(rel)
print("\n".join(missing))
PY

  if [ -s /tmp/_missing_jpgs.txt ]; then
    echo "[bootstrap] Downloading $(wc -l </tmp/_missing_jpgs.txt) missing JPG(s)..."
    # --cut-dirs=3 strips "files/mimic-cxr-jpg/2.1.0" from the URL path so
    # files land at "$JPG_ROOT/files/p10/..." (matching manifest paths).
    (
      cd "$JPG_ROOT"
      wget -r -N -c -np -nH --cut-dirs=3 \
        --user "$PN_USER" --password "$PN_PASS" \
        -i /tmp/_missing_jpgs.txt \
        --base="$PN_BASE_JPG/"
    )
  fi

  rm -f /tmp/_missing_jpgs.txt
  # Lock released when fd 9 closes at shell exit.
}

bootstrap_assets

python3 <<'PY'
import json
import os
from pathlib import Path

manifest = json.loads(Path("/opt/task_manifest.json").read_text())
subject_id = manifest["subject_id"]
group = f"p{subject_id[:2]}"

src_images = Path("/data/_src/jpg_root/files") / group / f"p{subject_id}"
patient_reports = Path("/data/_src/patient_reports")
dest = Path("/data/patient")
dest.mkdir(parents=True, exist_ok=True)

# Top-level manifest copy for agent reference
(dest / "manifest.json").write_text(json.dumps(manifest, indent=2))

for study in manifest["studies"]:
    sid = study["study_id"]
    folder = dest / study["folder"]
    folder.mkdir(parents=True, exist_ok=True)

    # Symlink JPGs from the shared dataset mount.
    study_src_dir = src_images / f"s{sid}"
    for view in study["views"]:
        src_jpg = study_src_dir / f"{view['dicom_id']}.jpg"
        dst_jpg = folder / f"{view['dicom_id']}.jpg"
        if dst_jpg.is_symlink() or dst_jpg.exists():
            continue
        os.symlink(src_jpg, dst_jpg)

    # Copy prior-study report (target is never present in patient_reports).
    if not study["is_target"]:
        src_txt = patient_reports / f"s{sid}.txt"
        if src_txt.exists():
            (folder / "report.txt").write_bytes(src_txt.read_bytes())
PY

exec "$@"
"""


#: Shared data root on the host. The JPG dataset and reports archive live
#: under this root in a layout that mirrors PhysioNet's directory structure.
#: Tasks mount the dataset roots (not a single patient dir) so the entrypoint
#: can download missing assets on first run.
DEFAULT_HOST_DATA_ROOT = (Path(__file__).parent / "assets").resolve()


def _generate_docker_compose(task: dict[str, Any], image_root: Path, reports_zip: Path) -> str:
    """Generate docker-compose.yaml for a single patient task.

    The compose file mounts the shared MIMIC-CXR data roots read-write so the
    entrypoint can bootstrap missing assets from PhysioNet (flock-guarded).
    In steady state, nothing is written — the mounts behave as read-only.

    PhysioNet credentials are passed through from the host shell environment
    (PN_USER / PN_PASS). If unset, the entrypoint skips downloads and assumes
    assets are already present.
    """
    subject_id = task["subject_id"]
    jpg_root_host = (DEFAULT_HOST_DATA_ROOT / "mimic-cxr-jpg" / "2.1.0").resolve()
    patient_reports_host = (
        DEFAULT_HOST_DATA_ROOT / "mimic-cxr" / "2.1.0" / "extracted" / f"p{subject_id}"
    ).resolve()

    # Per-patient reports dir is mounted rw. At generation time it is
    # pre-populated with ONLY this patient's prior-study `.txt` files.
    # If the host dir is empty (setup skipped), the entrypoint downloads
    # the full reports zip into /tmp, extracts only this patient's priors
    # into the mount, then removes the tmp zip so the agent never sees it.
    return f"""services:
  main:
    build:
      context: ..
      dockerfile: environment/Dockerfile
    volumes:
      - {jpg_root_host}:/data/_src/jpg_root:rw
      - {patient_reports_host}:/data/_src/patient_reports:rw
    environment:
      - PYTHONUNBUFFERED=1
      - PN_USER=${{PN_USER:-}}
      - PN_PASS=${{PN_PASS:-}}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
"""


def _generate_workspace_readme(task: dict[str, Any]) -> str:
    return f"""# Workspace — Report Generation

- `benchmark_tasks.json`: task definition with patient history and target study info
- `submission.json`: editable; fill in `final_answer` with generated report

Patient data is mounted at `/data/patient/` as timestamped folders:

    /data/patient/
      manifest.json                        # study index
      <timestamp>_s<study_id>/             # one folder per study, chronological
        <dicom_id>.jpg                     # chest X-ray image(s)
        report.txt                         # radiology report (PRIOR studies only)

The target study's folder contains only `.jpg` images — no `report.txt`.

Patient: {task['subject_id']}
Target study: {task['target_study']['study_id']}
Prior studies: {len(task['history'])}
"""


def _generate_test_script() -> str:
    return """#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
python verify_meta_task.py
"""


def _copy_evaluator(tests_dir: Path) -> None:
    evaluator_src = Path(__file__).parent / "harbor_evaluator.py"
    if evaluator_src.exists():
        (tests_dir / "evaluator.py").write_text(evaluator_src.read_text())


def _copy_verifier(tests_dir: Path) -> None:
    verifier_src = Path(__file__).parent / "verify_meta_task.py"
    if verifier_src.exists():
        (tests_dir / "verify_meta_task.py").write_text(verifier_src.read_text())


def _copy_labeler(tests_dir: Path) -> None:
    """Copy chexbert_labeler.py next to verify_meta_task.py.

    The verifier imports this module (inside the task container) to compute
    per-trial CheXbert label vectors, which then travel via reward.json to
    the aggregator as pooled scalar fields.
    """
    labeler_src = Path(__file__).parent / "chexbert_labeler.py"
    if labeler_src.exists():
        (tests_dir / "chexbert_labeler.py").write_text(labeler_src.read_text())


def _extract_prior_reports(
    *,
    manifest: dict[str, Any],
    source_zip: Path,
    extracted_root: Path,
) -> None:
    """Extract the patient's PRIOR-study reports into a shared per-patient dir.

    Produces:
        <extracted_root>/p<subject_id>/s<study_id>.txt  (one per prior study)

    The target study's report is intentionally never written. Existing files
    are left untouched — so repeated generation is cheap. The resulting
    per-patient directory is what each task's docker-compose bind-mounts
    read-write into the container at /data/_src/patient_reports.
    """
    import zipfile as _zipfile

    subject_id = manifest["subject_id"]
    group = f"p{subject_id[:2]}"
    patient_dir = extracted_root / f"p{subject_id}"
    patient_dir.mkdir(parents=True, exist_ok=True)

    prior_studies = [s for s in manifest["studies"] if not s["is_target"]]
    if not prior_studies:
        return
    needed = {s["study_id"] for s in prior_studies if not (patient_dir / f"s{s['study_id']}.txt").exists()}
    if not needed:
        return

    with _zipfile.ZipFile(source_zip) as zf:
        for sid in needed:
            arcname = f"files/{group}/p{subject_id}/s{sid}.txt"
            try:
                (patient_dir / f"s{sid}.txt").write_bytes(zf.read(arcname))
            except KeyError:
                # Missing prior report in the source zip — tolerate silently;
                # the entrypoint will simply not create report.txt for it.
                pass


def _jpg_status(path: Path) -> str:
    """Classify an on-disk JPG path for download planning.

    Returns one of:
      - "complete": file exists, non-zero, and ends with the JPEG EOI marker
        (0xFF 0xD9). Safe to skip.
      - "partial":  file exists and non-empty but lacks a valid EOI. Likely a
        half-downloaded file. `wget -c` can resume from current length.
      - "empty":    file exists but is 0 bytes. Deleted so wget starts fresh.
      - "missing":  file does not exist.
    """
    if not path.exists():
        return "missing"
    try:
        size = path.stat().st_size
    except OSError:
        return "missing"
    if size == 0:
        return "empty"
    try:
        with path.open("rb") as f:
            f.seek(-2, 2)
            tail = f.read(2)
    except OSError:
        return "partial"
    return "complete" if tail == b"\xff\xd9" else "partial"


def _download_images_for_tasks(
    tasks_and_manifests: list[tuple[str, dict[str, Any]]],
    assets_root: Path,
) -> None:
    """Download the per-patient JPG subset required by `tasks_and_manifests`.

    Looks at each task manifest, computes the expected host path under
    `assets_root/mimic-cxr-jpg/2.1.0/files/...`, classifies each into
    complete / partial / empty / missing, and runs a single flock-guarded
    `wget -c -i -` batch for anything that isn't complete. `wget -c`
    resumes partial files in-place from their existing byte offset.
    No-ops cleanly (with a warning) if `PN_USER`/`PN_PASS` are unset.
    """
    import os
    import subprocess

    jpg_root = assets_root / "mimic-cxr-jpg" / "2.1.0"
    jpg_root.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    complete_count = 0
    partial_paths: list[str] = []
    empty_paths: list[str] = []

    for _, manifest in tasks_and_manifests:
        subject_id = manifest["subject_id"]
        group = f"p{subject_id[:2]}"
        for study in manifest["studies"]:
            for view in study["views"]:
                rel = (
                    f"files/{group}/p{subject_id}/"
                    f"s{study['study_id']}/{view['dicom_id']}.jpg"
                )
                status = _jpg_status(jpg_root / rel)
                if status == "complete":
                    complete_count += 1
                    continue
                if status == "empty":
                    # 0-byte file — wget's `-c` would still append to it but an
                    # empty placeholder is the classic symptom of an interrupted
                    # download that never got its first byte; remove it so wget
                    # starts clean.
                    try:
                        (jpg_root / rel).unlink()
                    except OSError:
                        pass
                    empty_paths.append(rel)
                    missing.append(rel)
                elif status == "partial":
                    partial_paths.append(rel)
                    missing.append(rel)
                else:  # "missing"
                    missing.append(rel)

    print(
        f"  JPG inventory: {complete_count} complete, "
        f"{len(partial_paths)} partial (will resume), "
        f"{len(empty_paths)} empty (deleted + requeued), "
        f"{len(missing) - len(partial_paths) - len(empty_paths)} missing"
    )
    if partial_paths:
        print("    Partial JPGs flagged for resume:")
        for rel in partial_paths[:10]:
            try:
                sz = (jpg_root / rel).stat().st_size
            except OSError:
                sz = 0
            print(f"      {rel}  (have {sz} bytes; will resume)")
        if len(partial_paths) > 10:
            print(f"      ... and {len(partial_paths) - 10} more")
    if empty_paths:
        print("    Empty JPGs that were deleted + requeued:")
        for rel in empty_paths[:10]:
            print(f"      {rel}")
        if len(empty_paths) > 10:
            print(f"      ... and {len(empty_paths) - 10} more")

    if not missing:
        print("  ✓ All task JPGs already complete in assets")
        return

    pn_user = os.environ.get("PN_USER")
    pn_pass = os.environ.get("PN_PASS")
    if not pn_user or not pn_pass:
        print(
            f"  ⚠ {len(missing)} JPG(s) missing under {jpg_root} and "
            "PN_USER/PN_PASS unset — skipping download."
        )
        print(
            "    Task containers will attempt the same download on first run."
        )
        return

    lock_dir = assets_root / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / "mimic-cxr-setup.lock"

    import tempfile

    # Parallelize via chunked wget processes. Each chunk operates on a disjoint
    # file list, so there's no write contention between workers.
    n_workers = int(os.environ.get("MIMIC_DOWNLOAD_PARALLELISM", "8"))
    n_workers = max(1, min(n_workers, len(missing)))
    chunks = [missing[i::n_workers] for i in range(n_workers)]

    list_paths: list[str] = []
    for chunk in chunks:
        if not chunk:
            continue
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
            f.write("\n".join(chunk))
            list_paths.append(f.name)

    print(
        f"  Downloading {len(missing)} JPG(s) into {jpg_root} "
        f"with {len(list_paths)} parallel wget workers..."
    )

    quoted_lists = " ".join(f"'{p}'" for p in list_paths)
    # --cut-dirs=3 strips "files/mimic-cxr-jpg/2.1.0" from the server path so
    # downloads land at "$JPG_ROOT/files/p10/..." (matching the layout the
    # entrypoint expects). One outer flock(1) guards the whole batch; workers
    # then run concurrently on disjoint file lists.
    cmd = f"""
set -euo pipefail
exec 9>{lock_file}
flock 9
cd {jpg_root}
fail=0
for list_path in {quoted_lists}; do
  (
    wget -r -N -c -np -nH --cut-dirs=3 --quiet --show-progress \
      --user '{pn_user}' --password '{pn_pass}' \
      -i "$list_path" \
      --base='https://physionet.org/files/mimic-cxr-jpg/2.1.0/'
  ) &
done
for job in $(jobs -p); do
  wait "$job" || fail=1
done
exit "$fail"
"""
    result = subprocess.run(["bash", "-c", cmd])
    for lp in list_paths:
        Path(lp).unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"One or more wget workers failed (exit {result.returncode}). "
            "Check stderr; partial files are safe to retry — the next "
            "generator run will resume them in place."
        )
    print(f"  ✓ Downloaded {len(missing)} JPG(s)")


def _scaffold_task_dir(output_dir: Path) -> None:
    """Create the minimal directory structure that `harbor init` produces.

    We bypass the harbor CLI subprocess (~0.9s per call on this machine)
    because we overwrite every file it creates anyway. This skips the cost
    completely without changing the resulting layout.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "environment").mkdir(exist_ok=True)
    (output_dir / "environment" / "workspace").mkdir(exist_ok=True)
    (output_dir / "tests").mkdir(exist_ok=True)
    # Empty README so Harbor task discovery is happy
    readme = output_dir / "README.md"
    if not readme.exists():
        readme.write_text(f"# {output_dir.name}\n")


def _write_single_task(
    *,
    output_dir: Path,
    task_name: str,
    task: dict[str, Any],
    answer_key: dict[str, Any],
    image_root: Path,
    reports_zip: Path,
) -> None:
    """Write a complete Harbor task directory for one patient."""
    if output_dir.exists():
        shutil.rmtree(output_dir)

    _scaffold_task_dir(output_dir)

    # Clean scaffolding
    gitignore = output_dir / ".gitignore"
    if gitignore.exists():
        gitignore.unlink()

    # Root-level files
    output_dir.joinpath("task.toml").write_text(
        _generate_task_toml(task["task_id"], task["subject_id"])
    )
    output_dir.joinpath("instruction.md").write_text(
        _generate_instruction_md(task)
    )

    # Environment
    env_dir = output_dir / "environment"
    workspace_dir = env_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Manifest + entrypoint: container materializes /data/patient/ at runtime.
    # The patient's PRIOR-study reports are extracted into a shared host
    # directory under DEFAULT_HOST_DATA_ROOT so the compose mount only
    # exposes this patient's non-target reports to the agent.
    manifest = _build_task_manifest(task)
    _write_json(env_dir / "task_manifest.json", manifest)
    extracted_root = DEFAULT_HOST_DATA_ROOT / "mimic-cxr" / "2.1.0" / "extracted"
    _extract_prior_reports(
        manifest=manifest,
        source_zip=reports_zip,
        extracted_root=extracted_root,
    )
    entrypoint_path = env_dir / "entrypoint.sh"
    entrypoint_path.write_text(_generate_entrypoint())
    entrypoint_path.chmod(0o755)

    (env_dir / "Dockerfile").write_text(_generate_dockerfile())
    (env_dir / "docker-compose.yaml").write_text(
        _generate_docker_compose(task, image_root, reports_zip)
    )
    (workspace_dir / "README.md").write_text(_generate_workspace_readme(task))

    # benchmark_tasks.json — single-element list (agent-visible)
    _write_json(workspace_dir / "benchmark_tasks.json", [task])

    # submission.json — template for agent to fill
    submission = [
        {
            "task_id": task["task_id"],
            "instruction": task["instruction"],
            "final_answer": "",
            "payload": None,
        }
    ]
    _write_json(workspace_dir / "submission.json", submission)

    # Tests
    tests_dir = output_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    _write_json(tests_dir / "task_answer_key.json", [answer_key])
    _copy_evaluator(tests_dir)
    _copy_verifier(tests_dir)
    _copy_labeler(tests_dir)

    test_sh = tests_dir / "test.sh"
    test_sh.write_text(_generate_test_script())
    test_sh.chmod(0o755)


def generate_harbor_tasks(
    *,
    output_root: Path,
    meta_root: Path | None = None,
    image_root: Path | None = None,
    reports_zip: Path | None = None,
    sample_size: int | None = None,
    seed: int = 42,
    selected_subject_ids: list[str] | None = None,
    parallelism: int = 16,
) -> None:
    """Generate one Harbor task per patient.

    Args:
        output_root: Root directory under which task dirs are created.
        meta_root: Path to directory containing mimic-cxr-2.0.0-metadata.csv.gz.
        image_root: Path to JPG dataset root (with p10/p11/... subdirs).
        reports_zip: Path to mimic-cxr-reports.zip.
        sample_size: Number of patients to sample. ``None`` (default) keeps
            every eligible patient.
        seed: Random seed for deterministic sampling.
        selected_subject_ids: Explicit patient IDs (skip sampling if provided).
        parallelism: Number of worker threads for per-patient task generation.
    """
    meta_root = Path(meta_root or DEFAULT_META_ROOT).resolve()
    image_root = Path(image_root or DEFAULT_IMAGE_ROOT).resolve()
    reports_zip = Path(reports_zip or DEFAULT_REPORTS_ZIP).resolve()

    print(f"Metadata root: {meta_root}")
    print(f"Image root:    {image_root}")
    print(f"Reports zip:   {reports_zip}")

    print("Loading metadata...")
    metadata = load_metadata(meta_root)
    print(f"  Loaded {len(metadata)} DICOM rows")

    print("Building patient study index...")
    patient_studies = build_patient_studies(metadata)
    print(f"  {len(patient_studies)} patients total")

    if selected_subject_ids is None:
        print(
            "Selecting eligible patients (2+ studies, images + reports present, "
            "target study in TEST split, target has non-empty FINDINGS+IMPRESSION)..."
        )
        eligible = select_eligible_patients(
            patient_studies,
            image_root=image_root,
            reports_zip=reports_zip,
            meta_root=meta_root,
            min_studies=2,
            target_split="test",
            require_nonempty_findings_impression=True,
        )
        print(f"  {len(eligible)} eligible patients")
        if sample_size is None:
            selected = list(eligible)
        else:
            selected = sample_patients(eligible, sample_size=sample_size, seed=seed)
    else:
        selected = selected_subject_ids

    print(f"Generating {len(selected)} tasks...")

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    import zipfile as _zipfile
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time as _time

    from tqdm import tqdm

    def _process_one(subj_id: str) -> tuple[str, int, dict[str, Any]]:
        """Build + write a single patient's task. Opens the reports zip once."""
        studies = patient_studies[subj_id]
        with _zipfile.ZipFile(reports_zip) as zf:
            task = build_task_for_patient(subj_id, studies, reports_zip, zf=zf)
            answer_key = build_answer_key_for_patient(subj_id, studies, reports_zip, zf=zf)
        task_name = f"p{subj_id}_s{task['target_study']['study_id']}"
        _write_single_task(
            output_dir=output_root / task_name,
            task_name=task_name,
            task=task,
            answer_key=answer_key,
            image_root=image_root,
            reports_zip=reports_zip,
        )
        manifest = _build_task_manifest(task)
        return task_name, len(task["history"]), manifest

    # Parallelize across patients. Per-patient work is dominated by network IO
    # (reading the reports zip and copying the entrypoint manifest), so threads
    # scale almost linearly until the network mount saturates.
    errors: list[tuple[str, str]] = []
    completed: list[tuple[str, dict[str, Any]]] = []
    t0 = _time.time()
    with ThreadPoolExecutor(max_workers=parallelism) as pool:
        futures = {pool.submit(_process_one, subj): subj for subj in selected}
        with tqdm(
            total=len(selected),
            desc=f"Generating tasks (parallelism={parallelism})",
            unit="task",
        ) as pbar:
            for fut in as_completed(futures):
                try:
                    task_name, n_prior, manifest = fut.result()
                    completed.append((task_name, manifest))
                    pbar.set_postfix_str(f"latest={task_name} (priors={n_prior})")
                except Exception as e:
                    errors.append((futures[fut], str(e)))
                pbar.update(1)

    elapsed = _time.time() - t0
    print(f"\n✓ Generated {len(selected) - len(errors)}/{len(selected)} tasks at {output_root} in {elapsed:.1f}s")
    if errors:
        print(f"  {len(errors)} errors:")
        for subj, err in errors[:10]:
            print(f"    {subj}: {err}")

    # Download per-patient JPG subset into assets so task containers have the
    # data already present. If creds missing, containers bootstrap themselves.
    print("\nDownloading per-task JPG subset into assets...")
    _download_images_for_tasks(completed, DEFAULT_HOST_DATA_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Harbor tasks for MIMIC-CXR report generation"
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Root directory for generated Harbor task artifacts",
    )
    parser.add_argument(
        "--meta-root",
        default=str(DEFAULT_META_ROOT),
        help="Directory containing mimic-cxr-2.0.0-metadata.csv.gz",
    )
    parser.add_argument(
        "--image-root",
        default=str(DEFAULT_IMAGE_ROOT),
        help="Path to JPG dataset root (with p10/p11/... subdirs)",
    )
    parser.add_argument(
        "--reports-zip",
        default=str(DEFAULT_REPORTS_ZIP),
        help="Path to mimic-cxr-reports.zip",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of patients to sample. Omit (default) to include every eligible patient.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic sampling (default: 42)",
    )
    parser.add_argument(
        "--selected-subject-ids",
        help="Comma-separated patient IDs to include (overrides sampling)",
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=16,
        help="Worker threads for per-patient task generation (default: 16)",
    )

    args = parser.parse_args()

    selected_ids = None
    if args.selected_subject_ids:
        selected_ids = args.selected_subject_ids.split(",")

    generate_harbor_tasks(
        output_root=Path(args.output_root),
        meta_root=Path(args.meta_root),
        image_root=Path(args.image_root),
        reports_zip=Path(args.reports_zip),
        sample_size=args.sample_size,
        seed=args.seed,
        selected_subject_ids=selected_ids,
        parallelism=args.parallelism,
    )


if __name__ == "__main__":
    main()
