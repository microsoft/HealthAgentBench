#!/bin/bash
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

  # --- Target study's full report (verifier-only stash) ---
  # Fetch the target study's .txt to /tests/target_report.txt. /tests is
  # bind-mounted from the host's tasks/<task>/tests/ dir (gitignored).
  # Harbor mounts the same host dir into main only at verifier time, so
  # the agent never sees this file. bootstrap has PN_USER/PN_PASS env;
  # main does NOT — after bootstrap exits, no PhysioNet creds remain.
  local target_sid target_subj target_group
  target_sid="$(python3 -c 'import json; print(json.load(open("/opt/task_manifest.json"))["target_study_id"])')"
  target_subj="$subject_id"
  target_group="p${target_subj:0:2}"
  if [ ! -s /tests/target_report.txt ] && [ -n "${PN_USER:-}" ] && [ -n "${PN_PASS:-}" ]; then
    echo "[bootstrap] Fetching target study s${target_sid}.txt..."
    wget -q --no-clobber \
      --user "$PN_USER" --password "$PN_PASS" \
      -O /tests/target_report.txt \
      "$PN_BASE_REPORTS/files/${target_group}/p${target_subj}/s${target_sid}.txt" \
      || { rm -f /tests/target_report.txt; echo "[bootstrap] target report fetch failed"; }
    if [ -s /tests/target_report.txt ]; then
      chmod 444 /tests/target_report.txt 2>/dev/null || true
    fi
  fi

  # --- Patient-specific PRIOR reports ---
  # If any prior-study .txt is missing from the mount, fetch it directly
  # from PhysioNet's file tree (one small HTTP GET per missing study).
  # The target study's .txt is fetched into /tests/ above, NEVER into
  # the patient_reports mount the agent sees.
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
    for dicom_id in study["dicom_ids"]:
        jpg = sdir / f"{dicom_id}.jpg"
        if not jpg.exists():
            # Path that wget -nH --cut-dirs=1 expects: relative to jpg_root
            rel = f"files/{group}/p{subject_id}/s{study['study_id']}/{dicom_id}.jpg"
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

# NB: ReXRank's gold-findings JSON is NOT downloaded here. It contains the
# full reference report for every test-split study (including the FINDINGS
# the agent must generate), so it would be a leak if the agent could read
# it. The verifier's test.sh downloads it post-agent, into
# /data/rexrank/rexrank_test.json, just before scoring.

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

# Section ordering used when writing the target's partial report.txt.
# Anything outside this allowlist is dropped — defense in depth, in case
# the source report contains FINDINGS or IMPRESSION headers in unexpected
# positions.
TARGET_SECTION_ORDER = (
    "EXAMINATION",
    "INDICATION",
    "HISTORY",
    "TECHNIQUE",
    "COMPARISON",
)
FORBIDDEN_SECTIONS = {"FINDINGS", "IMPRESSION"}

# Parse the target's full report (staged at /tests/target_report.txt by
# bootstrap_assets) and pull out the non-findings sections. The agent
# never sees this file directly — the partial report.txt we write to
# /data/patient/<target>/ is built from the parsed sections.
import re as _re
_SECTION_RE = _re.compile(
    r"^[\s>]*(EXAMINATION|INDICATION|HISTORY|TECHNIQUE|COMPARISON|"
    r"FINDINGS|IMPRESSION|RECOMMENDATION|NOTIFICATION)\s*:\s*",
    flags=_re.IGNORECASE | _re.MULTILINE,
)

def _parse_sections(text: str) -> dict[str, str]:
    matches = list(_SECTION_RE.finditer(text))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[name] = text[start:end].strip()
    return out

target_given: dict[str, str] = {}
target_report_path = Path("/tests/target_report.txt")
if target_report_path.exists():
    target_given = _parse_sections(target_report_path.read_text())

for study in manifest["studies"]:
    sid = study["study_id"]
    folder = dest / study["folder"]
    folder.mkdir(parents=True, exist_ok=True)

    # Symlink JPGs from the shared dataset mount into the per-study
    # folder under OPAQUE names so the agent can't read the DICOM ID
    # off the filename. The PhysioNet original-name JPG lives in the
    # cache mount (rw); only the renamed symlink reaches /data/patient/.
    study_src_dir = src_images / f"s{sid}"
    for idx, dicom_id in enumerate(study["dicom_ids"], start=1):
        src_jpg = study_src_dir / f"{dicom_id}.jpg"
        dst_jpg = folder / f"view_{idx:02d}.jpg"
        if dst_jpg.is_symlink() or dst_jpg.exists():
            continue
        os.symlink(src_jpg, dst_jpg)

    rp = folder / "report.txt"
    if study["is_target"]:
        # Write a PARTIAL report.txt with everything except FINDINGS and
        # IMPRESSION. The agent reads this for clinical context and then
        # generates the two missing sections.
        body_lines = []
        for name in TARGET_SECTION_ORDER:
            if name in FORBIDDEN_SECTIONS:
                continue
            text = (target_given.get(name) or "").strip()
            if text:
                body_lines.append(f"{name}:")
                body_lines.append(text)
                body_lines.append("")
        rp.write_text("\n".join(body_lines).rstrip() + "\n")
    else:
        # Prior study: copy the full report from the per-patient mount.
        src_txt = patient_reports / f"s{sid}.txt"
        if src_txt.exists() and not rp.exists():
            rp.write_bytes(src_txt.read_bytes())
PY

# Bootstrap done. Exit 0 so the main service (which depends on this one
# via ``service_completed_successfully``) starts. The manifest was only
# bind-mounted into THIS container, so it disappears with us — main
# never sees it.
echo "[bootstrap] complete."
exit 0
