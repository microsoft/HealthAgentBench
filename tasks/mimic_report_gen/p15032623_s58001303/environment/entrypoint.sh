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
