#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Bootstrap any missing MIMIC-CXR assets for this task from PhysioNet.
#
# Mounts:
#   /data/_src/jpg_root              → mimic-cxr-jpg/2.1.0 dataset root (rw,
#                                       shared). Holds the metadata CSV, the
#                                       JPG files/ tree, and — created on
#                                       first run if missing —
#                                       id_translation.csv.
#   /data/_src/patient_reports_root  → whole extracted/ prior-reports tree
#                                       (rw, host-populated; navigate by real
#                                       subject_id at runtime)
#
# Every MIMIC ID in the committed manifest (subject_id, study_id, dicom_ids)
# is a salted SHA256 hash. Real IDs live ONLY in the gitignored
# id_translation.csv (under jpg_root/) and never get baked into committed
# files. Bootstrap generates that translation table from
# mimic-cxr-2.0.0-metadata.csv.gz the first time a container comes up on a
# fresh host — no host-side ``hash_mimic_ids.py`` step required.
# ---------------------------------------------------------------------------
MANIFEST=/opt/task_manifest.json
JPG_ROOT=/data/_src/jpg_root
PATIENT_REPORTS_ROOT=/data/_src/patient_reports_root
ID_TRANSLATION="$JPG_ROOT/id_translation.csv"
SRC_IMAGES="$JPG_ROOT/files"
DEST=/data/patient

PN_BASE_REPORTS="https://physionet.org/files/mimic-cxr/2.1.0"
PN_BASE_JPG="https://physionet.org/files/mimic-cxr-jpg/2.1.0"

mkdir -p "$DEST"

# ---------------------------------------------------------------------------
# Translation helper. The manifest stores HASHED IDs; the rest of bootstrap
# needs the REAL IDs to talk to PhysioNet. We write a tiny Python module to
# /opt/_translate.py at startup so each downstream Python heredoc can
# ``import`` it with a single line instead of duplicating the loader.
# ---------------------------------------------------------------------------
cat > /opt/_translate.py <<'TRANSLATE_PY'
# Translate hashed MIMIC IDs back to real IDs using the translation CSV
# in the jpg_root cache. Loaded lazily on first call.
import csv
from pathlib import Path

_TABLE_PATH = Path("/data/_src/jpg_root/id_translation.csv")
_MAPS: dict[str, dict[str, str]] = {}

def _load() -> None:
    global _MAPS
    if _MAPS:
        return
    _MAPS = {"subject": {}, "study": {}, "dicom": {}}
    with _TABLE_PATH.open() as f:
        r = csv.reader(f); next(r)
        for kind, real, hashed in r:
            if kind in _MAPS:
                _MAPS[kind][hashed] = real

def real(kind: str, hashed: str) -> str:
    _load()
    try:
        return _MAPS[kind][hashed]
    except KeyError as exc:
        raise KeyError(
            f"No translation for hashed {kind} id {hashed!r}; "
            f"id_translation.csv may be stale."
        ) from exc
TRANSLATE_PY

ensure_translation_csv() {
  # Build $ID_TRANSLATION from the MIMIC metadata CSV if it's missing.
  # Idempotent + flock-guarded so concurrent trial bootstraps don't race.
  if [ -s "$ID_TRANSLATION" ]; then
    return 0
  fi
  mkdir -p "$JPG_ROOT" "$JPG_ROOT/.bootstrap.locks"
  local lf="$JPG_ROOT/.bootstrap.locks/id_translation.lock"
  exec 8>"$lf"
  flock 8
  if [ -s "$ID_TRANSLATION" ]; then
    exec 8>&-
    return 0
  fi
  local meta="$JPG_ROOT/mimic-cxr-2.0.0-metadata.csv.gz"
  if [ ! -s "$meta" ]; then
    if [ -z "${PN_USER:-}" ] || [ -z "${PN_PASS:-}" ]; then
      echo "[bootstrap] FATAL: $ID_TRANSLATION missing and PN_USER/PN_PASS unset; cannot build it." >&2
      exec 8>&-
      return 1
    fi
    echo "[bootstrap] Downloading $(basename "$meta") to build id_translation.csv..."
    wget -q --user "$PN_USER" --password "$PN_PASS" -O "$meta" \
      "$PN_BASE_JPG/$(basename "$meta")"
  fi
  echo "[bootstrap] Building id_translation.csv from $(basename "$meta")..."
  python3 - "$meta" "$ID_TRANSLATION" <<'PY'
import csv, gzip, hashlib, sys
meta_path, out_path = sys.argv[1], sys.argv[2]
# IMPORTANT: keep the SALT identical to scripts/xray_report_correction/
# hash_mimic_ids.py — committed manifest hashes are derived from this salt.
SALT = "medcli-xray-report-correction-v1"
HASH_LEN = 16
def h(real):
    return hashlib.sha256(f"{SALT}|{real}".encode()).hexdigest()[:HASH_LEN]
subjects, studies, dicoms = set(), set(), set()
with gzip.open(meta_path, "rt", newline="") as f:
    for row in csv.DictReader(f):
        if s := row.get("subject_id"): subjects.add(s)
        if s := row.get("study_id"):   studies.add(s)
        if s := row.get("dicom_id"):   dicoms.add(s)
with open(out_path + ".tmp", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kind", "real", "hash"])
    for s in sorted(subjects): w.writerow(["subject", s, h(s)])
    for s in sorted(studies):  w.writerow(["study", s, h(s)])
    for s in sorted(dicoms):   w.writerow(["dicom", s, h(s)])
import os
os.replace(out_path + ".tmp", out_path)
print(f"[bootstrap] wrote {out_path} (subjects={len(subjects)}, studies={len(studies)}, dicoms={len(dicoms)})")
PY
  exec 8>&-
}

bootstrap_assets() {
  ensure_translation_csv

  # Per-patient lock: concurrent task containers for DIFFERENT patients
  # bootstrap in parallel (disjoint file subtrees), while tasks for the
  # SAME patient still serialize (guards against self-races).
  local subject_id
  # Read hashed subject_id from manifest, translate to real for the
  # per-patient lock so concurrent trials of the SAME patient still
  # serialize (the host cache is keyed by real subject_id).
  subject_id="$(python3 -c 'import sys, json; sys.path.insert(0, "/opt"); from _translate import real; m=json.load(open("/opt/task_manifest.json")); print(real("subject", m["subject_id"]))')"
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
  # Translate hashed target_study_id → real for the PhysioNet URL.
  target_sid="$(python3 -c 'import sys, json; sys.path.insert(0, "/opt"); from _translate import real; m=json.load(open("/opt/task_manifest.json")); print(real("study", m["target_study_id"]))')"
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
import json, sys
from pathlib import Path
sys.path.insert(0, "/opt")
from _translate import real

m = json.loads(Path("/opt/task_manifest.json").read_text())
# Translate hashed manifest IDs → real for PhysioNet URLs and the
# per-patient cache subdir.
subj = real("subject", m["subject_id"])
group = f"p{subj[:2]}"
dest = Path("/data/_src/patient_reports_root") / f"p{subj}"
dest.mkdir(parents=True, exist_ok=True)
for study in m["studies"]:
    if study["is_target"]:
        continue
    sid = real("study", study["study_id"])
    if not (dest / f"s{sid}.txt").exists():
        # PhysioNet URL-relative path (resolved via --base)
        print(f"files/{group}/p{subj}/s{sid}.txt")
PY
    if [ -s /tmp/_missing_reports.txt ]; then
      echo "[bootstrap] Fetching $(wc -l </tmp/_missing_reports.txt) missing prior report(s)..."
      (
        # Each URL writes to its basename in cwd, so we cd into the
        # per-patient cache dir keyed by REAL subject_id. The Python
        # heredoc above already mkdir'd it.
        cd "$PATIENT_REPORTS_ROOT/p${subject_id}"
        wget -c -N \
          --user "$PN_USER" --password "$PN_PASS" \
          -i /tmp/_missing_reports.txt \
          --base="$PN_BASE_REPORTS/"
      )
    fi
    rm -f /tmp/_missing_reports.txt
  elif ! ls "$PATIENT_REPORTS_ROOT/p${subject_id}"/s*.txt >/dev/null 2>&1; then
    echo "[bootstrap] patient_reports empty and PN_USER/PN_PASS not set — agent will see no prior reports."
  fi

  # --- Per-study JPGs listed in the manifest ---
  if [ -z "${PN_USER:-}" ] || [ -z "${PN_PASS:-}" ]; then
    echo "[bootstrap] PN_USER/PN_PASS not set; skipping JPG download."
    return 0
  fi

  python3 - <<'PY' > /tmp/_missing_jpgs.txt
import json, os, sys
from pathlib import Path
sys.path.insert(0, "/opt")
from _translate import real

m = json.loads(Path("/opt/task_manifest.json").read_text())
# All IDs in the manifest are HASHED — translate before constructing
# PhysioNet paths.
subject_id = real("subject", m["subject_id"])
group = f"p{subject_id[:2]}"
root = Path("/data/_src/jpg_root/files") / group / f"p{subject_id}"
missing = []
for study in m["studies"]:
    sid = real("study", study["study_id"])
    sdir = root / f"s{sid}"
    for dicom_id_hash in study["dicom_ids"]:
        dicom_id = real("dicom", dicom_id_hash)
        jpg = sdir / f"{dicom_id}.jpg"
        if not jpg.exists():
            # Path that wget -nH --cut-dirs=1 expects: relative to jpg_root
            rel = f"files/{group}/p{subject_id}/s{sid}/{dicom_id}.jpg"
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
import os, sys
from pathlib import Path
sys.path.insert(0, "/opt")
from _translate import real

manifest = json.loads(Path("/opt/task_manifest.json").read_text())
# Translate hashed manifest IDs back to real for filesystem layout.
subject_id = real("subject", manifest["subject_id"])
group = f"p{subject_id[:2]}"

src_images = Path("/data/_src/jpg_root/files") / group / f"p{subject_id}"
patient_reports = Path("/data/_src/patient_reports_root") / f"p{subject_id}"
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
    # Translate hashed IDs to real for path lookups.
    sid = real("study", study["study_id"])
    folder = dest / study["folder"]
    folder.mkdir(parents=True, exist_ok=True)

    # Copy JPGs from the shared dataset mount into the per-study folder
    # under OPAQUE names so the agent can't read the DICOM ID off the
    # filename. We deliberately COPY (rather than symlink) so the agent
    # container doesn't need the jpg_root cache mounted at all — the
    # files live in the ``patient-data`` named volume produced by
    # bootstrap. This avoids:
    #   * broken symlinks when main lacks the jpg_root mount
    #   * the agent following a symlink target back into the cache dir
    #     and seeing dataset-wide CSVs (chexpert.csv.gz, metadata.csv.gz,
    #     split.csv.gz) that would let it bypass the radiology task
    #
    # Cost is modest: each JPG is ~1-3 MB and each task carries at most a
    # handful of views per study; the named volume is per-trial and
    # disposed at trial cleanup.
    import shutil as _shutil
    study_src_dir = src_images / f"s{sid}"
    for idx, dicom_id_hash in enumerate(study["dicom_ids"], start=1):
        dicom_id = real("dicom", dicom_id_hash)
        src_jpg = study_src_dir / f"{dicom_id}.jpg"
        dst_jpg = folder / f"view_{idx:02d}.jpg"
        if dst_jpg.exists() and not dst_jpg.is_symlink():
            continue
        if dst_jpg.is_symlink():
            dst_jpg.unlink()
        _shutil.copyfile(src_jpg, dst_jpg)

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
        r'^[\s>]*FINDINGS:\s*(.*?)(?=^[\s>]*(IMPRESSION|NOTIFICATION|RECOMMENDATION):|\Z)',
        report_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not m:
        raise ValueError("gold report has no FINDINGS section")
    paragraphs = re.split(r'\n\s*\n', m.group(1))
    normalized = []
    for p in paragraphs:
        p_clean = re.sub(r'\s+', ' ', p).strip()
        if p_clean:
            normalized.append(p_clean)
    return '\n\n'.join(normalized)


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
            block = "\nFINDINGS:\n" + draft + "\n"
            rp.write_text(existing.rstrip() + block)
            print(
                f"[bootstrap] synthesized DRAFT FINDINGS via {len(rules)} swaps "
                f"({len(draft)} chars) into {rp}"
            )
            break
PY

echo "[bootstrap] complete."
exit 0
