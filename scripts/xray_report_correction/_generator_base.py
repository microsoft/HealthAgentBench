#!/usr/bin/env python3
"""Generate Harbor tasks for MIMIC-CXR report generation benchmark.

Each task is one patient. The agent sees:
  - All prior studies: JPG images + reports + timestamps
  - Target study: JPG images + timestamps (NO report)
The agent must generate the target study's radiology report.

Data sources (all downloaded from PhysioNet on first run by
``scripts/xray_report_correction/setup.sh`` and the per-task ``bootstrap``
compose service into ``scripts/xray_report_correction/assets/`` — gitignored):
  - Metadata: ``mimic-cxr-2.0.0-metadata.csv.gz`` from
    ``physionet.org/files/mimic-cxr/2.1.0/``
  - Images (JPG): per-patient subdirs from
    ``physionet.org/files/mimic-cxr-jpg/2.1.0/files/``
  - Reports (zip): ``mimic-cxr-reports.zip`` from
    ``physionet.org/files/mimic-cxr/2.1.0/``

At generation time, prior reports are extracted from the zip and baked into the
task workspace at environment/workspace/reports/s<study>.txt. Only JPG image
directories are mounted from the host. The target study's report is never
extracted or mounted; it lives only in tests/task_answer_key.json.

Usage (default: every eligible patient, latest study as target):
    python scripts/xray_report_correction/generate_harbor_tasks.py \
      --output-root tasks/xray_report_correction

Usage (custom sample size):
    python scripts/xray_report_correction/generate_harbor_tasks.py \
      --output-root tasks/xray_report_correction \
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
    CHEXPERT14_LABELS,
    DEFAULT_IMAGE_ROOT,
    DEFAULT_META_ROOT,
    DEFAULT_REPORTS_ZIP,
    _build_instruction,
    build_answer_key_for_patient,
    build_patient_studies,
    build_task_for_patient,
    disease_stratified_sample,
    tiered_disease_stratified_sample,
    load_chexpert_labels,
    load_metadata,
    sample_patients,
    select_eligible_patients,
)


_ID_TRANSLATION_CSV = (
    Path(__file__).resolve().parent
    / "assets" / "mimic-cxr-jpg" / "2.1.0" / "id_translation.csv"
)


def _load_translation_maps() -> dict[str, dict[str, dict[str, str]]]:
    """Load the real↔hash translation table from assets/id_translation.csv.

    Returns a nested dict keyed by ID kind (``subject``, ``study``,
    ``dicom``) with two sub-dicts each: ``r2h`` (real → hash) and ``h2r``
    (hash → real). The CSV is gitignored and produced by
    ``hash_mimic_ids.py``; without it the generator cannot translate the
    hashed ``CURATED_CASES`` entries back to real MIMIC IDs for downloads
    and metadata lookups.

    Auto-runs ``hash_mimic_ids.py`` if the translation CSV is missing so
    the user only needs to invoke ``generate_harbor_tasks.py`` to bring
    up a fresh tree on a new host.
    """
    if not _ID_TRANSLATION_CSV.is_file():
        print(
            f"[generator] {_ID_TRANSLATION_CSV.name} missing — "
            f"building it from the MIMIC metadata CSV (one-time)..."
        )
        # Local import to avoid forcing the dependency at module-load time.
        import importlib.util as _util
        spec = _util.spec_from_file_location(
            "hash_mimic_ids", Path(__file__).resolve().parent / "hash_mimic_ids.py"
        )
        if spec is None or spec.loader is None:
            raise SystemExit("Could not load hash_mimic_ids.py for auto-build.")
        mod = _util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rc = mod.main()
        if rc != 0 or not _ID_TRANSLATION_CSV.is_file():
            raise SystemExit(
                f"hash_mimic_ids.py exited {rc} and {_ID_TRANSLATION_CSV} "
                f"is still missing — run it manually to diagnose."
            )
    import csv
    maps: dict[str, dict[str, dict[str, str]]] = {
        "subject": {"r2h": {}, "h2r": {}},
        "study": {"r2h": {}, "h2r": {}},
        "dicom": {"r2h": {}, "h2r": {}},
    }
    with _ID_TRANSLATION_CSV.open() as f:
        reader = csv.reader(f)
        next(reader)  # header
        for kind, real, hashed in reader:
            if kind in maps:
                maps[kind]["r2h"][real] = hashed
                maps[kind]["h2r"][hashed] = real
    return maps


# Curated MIMIC-CXR cases. The ground-truth reports for these five
# (subject_id, target study_id) pairs were manually reviewed for
# clinical accuracy before being added here.
#
# Use the ``--curated`` flag to build these (and only these) under
# --output-root. Each entry maps an *opaque* case name (what the agent
# and Harbor see) to the real MIMIC-CXR (subject_id, target study_id)
# — what the bootstrap container uses behind the scenes to fetch from
# PhysioNet. Subject + study + comments are all the generator needs;
# everything else (study dates, prior list, DICOM IDs) is read from
# MIMIC's ``mimic-cxr-2.0.0-metadata.csv.gz`` at generation time. The
# agent never sees these IDs — folders are renamed to opaque tokens.
CURATED_CASES: list[tuple[str, str, str]] = [
    # Curated MIMIC cases for x-ray report generation.
    #
    # IDs are 16-char SHA256 hashes (salted) of the real MIMIC subject_id
    # and target study_id. See ``hash_mimic_ids.py``. The translation back
    # to real IDs only happens at runtime via
    # ``assets/id_translation.csv`` (gitignored). Committing only the
    # hashes keeps all MIMIC IDs out of the repository.
    #
    # Bar: gold report has **0 clinically-significant errors** per radeval
    # expert annotation (sig=0), and the insignificant flags (where
    # present) are either pure completeness preferences or minor
    # interpretive nits. Cases where the gold itself had factual issues —
    # wrong lateralization / severity, missed surgical hardware
    # (sternotomy, valve prostheses), suspected hallucinations of priors
    # or removed tubes — were filtered out by manual review even when the
    # rubric reported fa=5.
    #
    # First five: longitudinal — have ≥1 prior study available in MIMIC.
    ("case_01", "30ac0a8d620cf048", "929deb7da7ff7c44"),  # clear lungs, hyperinflation
    ("case_02", "2b6fd83fced8bdf9", "aa2d09289517664b"),  # stable cardiomegaly, no acute change
    ("case_03", "90e37e2d44690a9c", "9b5627d4081112ea"),  # chest tubes, soft-tissue air
    ("case_04", "8fcb914377296a4f", "4dd0bc3e066d66b4"),  # ETT + IABP position
    ("case_05", "f7cfc087675917a5", "0331e0f1e3c47fb8"),  # fluid overload, ETT/NG/Cordis lines
    # Additional five: same bar, mix of longitudinal and single-study cases.
    ("case_06", "df355fcce55aaa49", "25ace4088f6c92e5"),  # no prior; cleanest gold (0 insig, fa=5)
    ("case_07", "74f1fddc1d623be3", "4ce579a2b784f9a2"),  # prior; insig = pneumo/effusion negation omissions only
    ("case_08", "6469a99a0f96ef55", "b43b403b27b2c307"),  # no prior; insig = cardiac-size omission only
    ("case_09", "2b6fd83fced8bdf9", "99f51f53c93aef99"),  # prior; minor interpretive nit on edema improvement
    ("case_10", "32ba56d7a694620f", "f3557de94145a347"),  # prior; insig = prior-opacity reference omission only
]
CURATED_STUDY_IDS: list[str] = [sid for _, _, sid in CURATED_CASES]


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2))


def _generate_task_toml(task_id: str, subject_id: str) -> str:
    # task.toml stays generic — no corpus name, no subject_id. The
    # benchmark label is opaque so the agent (if it inspects task.toml)
    # can't search the web for the source dataset. The verifier matches
    # ``task_id`` against tests/task_answer_key.json so the opaque value
    # must be consistent across all three files.
    return f"""version = "1.0"

[metadata]
benchmark = "radiology_report"
mode = "single-task"
description = "Generate a radiology report for the latest study in /data/patient/"
task_id = "{task_id}"
submission_path = "/workspace/submission.json"

[verifier]
timeout_sec = 900.0

[agent]
timeout_sec = 3600.0

[environment]
# Cold build installs the tiny chexprompt + openai==0.28 verifier venv
# (~30 s) and apt deps (~2 min). Pinning generously.
build_timeout_sec = 1800.0
allow_internet = true
cpus = 2
memory_mb = 4096
storage_mb = 10240
gpus = 0
mcp_servers = []
"""


def _generate_instruction_md(task: dict[str, Any]) -> str:
    # Single source of truth — render the same prose used in
    # submission.json's "instruction" field so the agent gets consistent
    # guidance whether it reads instruction.md or submission.json.
    # Deliberately does NOT enumerate priors or inline the target's
    # non-findings sections — those live in /data/patient/<...>/report.txt
    # and are discovered by the agent at run time.
    return task.get("instruction", "").rstrip() + "\n"


def _generate_dockerignore() -> str:
    """A ``.dockerignore`` at the task root (build context = ``..``)
    keeps verifier-only assets out of the build tarball. Even if a future
    Dockerfile edit adds ``COPY .`` by accident, the gold target report
    and answer key cannot make it into the image because they're never
    sent to the build daemon.
    """
    return """# Verifier-only assets — never bake into the agent image.
tests/
# Hidden caches / dotfiles
.git/
__pycache__/
*.pyc
"""


def _generate_dockerfile() -> str:
    # The image is shared between the ``bootstrap`` and ``main`` compose
    # services. bootstrap runs ``/bootstrap.sh`` (bind-mounted with the
    # task manifest at runtime, NOT baked into the image) to stage data
    # into named volumes; main runs the agent and then the verifier.
    #
    # The image never contains:
    #   * the task manifest (subject/study identifiers) — bind-mounted
    #     into bootstrap only,
    #   * PhysioNet credentials — env-passed to bootstrap only,
    #   * the gold target report — written to a named volume by bootstrap.
    return """FROM python:3.12-slim

# bash, curl/wget, flock for the bootstrap script. git is needed for the
# verifier-venv's `pip install git+...chexprompt`. ripgrep + jq are
# convenience tools the agent often needs.
RUN apt-get update && apt-get install -y --no-install-recommends \\
    bash \\
    curl \\
    wget \\
    git \\
    util-linux \\
    jq \\
    ripgrep \\
    && rm -rf /var/lib/apt/lists/*

# Verifier-only venv: chexprompt + the legacy openai==0.28 SDK pin it
# requires. Isolated from anything the agent might install at runtime.
RUN python -m venv /opt/verifier-venv \\
    && /opt/verifier-venv/bin/pip install --no-cache-dir --upgrade pip \\
    && /opt/verifier-venv/bin/pip install --no-cache-dir \\
        'openai==0.28.0' \\
        'aiolimiter>=1.1.0' \\
        'git+https://github.com/microsoft/chexprompt.git@main'

# Don't write .pyc files anywhere — keeps the bind-mounted /tests dir free
# of root-owned __pycache__ residue.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

# Only the empty workspace skeleton is baked in; everything else is
# populated by the bootstrap service via named compose volumes.
COPY environment/workspace/ /workspace/
RUN mkdir -p /logs/verifier /data/patient

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive for the
# agent + verifier. The bootstrap service uses an explicit ``command:``
# in docker-compose.yaml to run /bootstrap.sh (bind-mounted) and exit.
"""


def _timestamp_folder_name(study_datetime: str, study_id: str) -> str:
    """Produce a filesystem-safe folder name like '2180-05-06_21-30-14_s50414267'."""
    safe = study_datetime.replace(" ", "_").replace(":", "-")
    return f"{safe}_s{study_id}"


def _build_task_manifest(task: dict[str, Any]) -> dict[str, Any]:
    """Build the minimal manifest consumed by the entrypoint at container
    startup. Only the fields the runtime actually uses are persisted —
    descriptive metadata (study_datetime, procedure, view_position) is
    dropped because the agent doesn't need it, the entrypoint doesn't
    need it, and the verifier doesn't need it. Folder names already
    encode the timestamp, so chronological ordering is preserved.

    The entrypoint uses this manifest plus the target's full report
    (fetched on-the-fly to ``/tests/target_report.txt``) to:
      * symlink JPGs from the read-only mount into per-study folders,
      * write each prior study's full report.txt into its folder,
      * write the TARGET study's PARTIAL report.txt (allowlisted
        non-findings sections only) into its folder.
    """
    subject_id = task["subject_id"]
    target = task["target_study"]
    target_study_id = target["study_id"]
    all_studies = task["history"] + [target]
    # Sort priors chronologically before assigning opaque indices so the
    # target is always last.
    studies_sorted = sorted(all_studies, key=lambda s: s.get("study_datetime", ""))

    def _folder_for(idx: int, dt_str: str) -> str:
        # Encode the study's actual timestamp directly in the folder
        # name so the agent can see both absolute and relative timing
        # (interval-between-studies). Colons aren't filesystem-safe in
        # every context, so we rewrite ``HH:MM:SS`` → ``HH-MM-SS``.
        # Falls back to ``study_NN_no_date`` when no timestamp exists.
        ts = (dt_str or "").strip().replace(":", "-").replace(" ", "_")
        if not ts:
            return f"study_{idx + 1:02d}_no_date"
        return f"study_{idx + 1:02d}_{ts}"

    # Hash every MIMIC ID before it lands in the committed manifest.
    # Bootstrap translates these back to real IDs at runtime via the
    # bind-mounted ``/data/_src/id_translation.csv``.
    T = _load_translation_maps()
    return {
        "subject_id": T["subject"]["r2h"][str(subject_id)],
        "target_study_id": T["study"]["r2h"][str(target_study_id)],
        "studies": [
            {
                "folder": _folder_for(idx, s.get("study_datetime", "")),
                "study_id": T["study"]["r2h"][str(s["study_id"])],
                "is_target": s["study_id"] == target_study_id,
                "dicom_ids": [T["dicom"]["r2h"][v["dicom_id"]] for v in s["views"]],
            }
            for idx, s in enumerate(studies_sorted)
        ],
    }


def _generate_bootstrap_sh() -> str:
    """Generate the bootstrap script run by the ``bootstrap`` compose
    service before ``main`` starts.

    The manifest is bind-mounted at /opt/task_manifest.json — NOT baked
    into the image — so the main container never carries identifying
    information. PN_USER / PN_PASS are env-passed to this service only.

    Responsibilities:
      * Fetch any missing JPGs and prior reports from PhysioNet (cached
        on host bind mounts so re-runs are idempotent).
      * Fetch the target study's full report to /opt/gold/target_report.txt
        (a named compose volume the main container mounts read-only at
        verifier time).
      * Materialize /data/patient/<folder>/ for every study via a named
        compose volume the main container will mount. Each folder gets
        the appropriate JPG symlinks; prior folders get the full
        report.txt; the target folder gets a PARTIAL report.txt with
        every section EXCEPT FINDINGS + IMPRESSION (allowlist filter).

    Exits 0 on success so ``depends_on: service_completed_successfully``
    lets the main service start.
    """
    return r"""#!/bin/bash
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
echo "[bootstrap] complete."
exit 0
"""


#: Shared data root on the host. The JPG dataset and reports archive live
#: under this root in a layout that mirrors PhysioNet's directory structure.
#: Tasks mount the dataset roots (not a single patient dir) so the entrypoint
#: can download missing assets on first run.
DEFAULT_HOST_DATA_ROOT = (Path(__file__).parent / "assets").resolve()


def _generate_docker_compose(task: dict[str, Any], image_root: Path, reports_zip: Path) -> str:
    """Generate docker-compose.yaml for a single patient task.

    Two-service pattern (mirrors tasks/ehrshot/<task>/environment/):

      * ``bootstrap`` (one-shot) — PhysioNet credentials, bind-mounted
        task manifest + bootstrap.sh, host caches for JPG + prior
        reports. Materializes /data/patient via the ``patient-data``
        named volume and writes the gold target report into the
        host-side ``tests/`` dir via a bind mount. Exits 0 when done.

      * ``main`` (long-running) — depends on bootstrap's successful
        exit. Mounts /data/patient read-only (no PN creds, no manifest,
        no /tests during agent runtime). Has OpenAI creds for the
        verifier step. Harbor auto-mounts ``../tests:/tests`` only when
        invoking test.sh (its convention), so the agent never sees the
        gold target report; the verifier does.
    """
    # The compose file used to bake the patient subject_id into the
    # bind-mount path (``extracted/p<subject_id>``). That leaked a MIMIC
    # ID into a committed file. We now mount the whole ``extracted/``
    # parent dir into bootstrap and let bootstrap navigate to the right
    # subdir after translating the hashed manifest ID → real subject_id
    # via the bind-mounted translation CSV. No MIMIC IDs reach this
    # template.
    #
    # tasks/xray_report_correction/<task>/environment/  → repo root via ../../../../
    jpg_root_host = "../../../../scripts/xray_report_correction/assets/mimic-cxr-jpg/2.1.0"
    patient_reports_root_host = (
        "../../../../scripts/xray_report_correction/assets/mimic-cxr/2.1.0/extracted"
    )
    # Credentials are loaded via ``env_file`` from the repo-root .env so
    # the user doesn't need to ``export PN_USER=... PN_PASS=...`` before
    # running ``uv run harbor run``. The path
    # ``../../../../.env`` resolves from this compose file's location
    # (tasks/xray_report_correction/<task>/environment/) up to the repo root.
    return f"""services:
  bootstrap:
    image: ${{COMPOSE_PROJECT_NAME}}-main
    build:
      context: ..
      dockerfile: environment/Dockerfile
    env_file:
      # PN_USER / PN_PASS (PhysioNet) live here. Optional vars in .env
      # that we don't need are passed through harmlessly.
      - ../../../../.env
    volumes:
      # Task manifest bind-mounted into bootstrap ONLY. The main image
      # never carries patient/study identifiers in any form.
      - ./task_manifest.json:/opt/task_manifest.json:ro
      - ./bootstrap.sh:/bootstrap.sh:ro
      # Host bind caches: shared across trials so JPGs / prior reports
      # are downloaded at most once. ``patient_reports_root`` holds the
      # whole extracted/ dir (every patient) so the bind-mount path
      # carries no subject-specific ID. The id_translation.csv lives
      # inside ``jpg_root`` (mimic-cxr-jpg/2.1.0/id_translation.csv) so
      # it rides on the same mount — no separate bind needed. Bootstrap
      # auto-generates it from the metadata CSV at startup when missing.
      - {jpg_root_host}:/data/_src/jpg_root:rw
      - {patient_reports_root_host}:/data/_src/patient_reports_root:rw
      # Per-task tests/ dir is bind-mounted RW so bootstrap can write
      # target_report.txt into it. Harbor mounts the same host dir into
      # main as /tests when invoking the verifier; main's agent runtime
      # does NOT have /tests mounted. The host tests/ file is gitignored.
      - ../tests:/tests:rw
      # /data/patient is shared with main via a named compose volume.
      - patient-data:/data/patient:rw
    environment:
      - PYTHONUNBUFFERED=1
    command: ["/bin/bash", "/bootstrap.sh"]

  main:
    image: ${{COMPOSE_PROJECT_NAME}}-main
    build:
      context: ..
      dockerfile: environment/Dockerfile
    depends_on:
      bootstrap:
        condition: service_completed_successfully
    env_file:
      # OPENAI_API_KEY, OPENAI_BASE_URL, CHEXPROMPT_DEPLOYMENT (verifier).
      # NOTE: PN_USER / PN_PASS in the same .env do get loaded into main
      # by docker compose, but the verifier doesn't read them — the
      # bootstrap service is what touches PhysioNet. The agent has shell
      # access; if PN-credential isolation matters more, split .env into
      # two files and reference them per-service.
      - ../../../../.env
    volumes:
      # Agent-visible (read-only): patient images + reports staged by
      # bootstrap. The named ``patient-data`` volume holds REAL JPG file
      # copies (not symlinks back into /data/_src/jpg_root), so main
      # needs no other mounts to read images. This intentionally cuts
      # main off from the dataset-wide CSVs that live next to the JPG
      # cache (chexpert / metadata / split) — those carry gold labels
      # for every study and would let the agent bypass the X-ray.
      - patient-data:/data/patient:ro
    environment:
      - PYTHONUNBUFFERED=1
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

volumes:
  patient-data:
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

Prior studies: {len(task['history'])}
"""


def _generate_test_script() -> str:
    # Gold FINDINGS + IMPRESSION are baked into tests/task_answer_key.json
    # at generation time (host has the credentialed MIMIC reports zip).
    # The verifier reads them directly — no network calls from inside the
    # container, no ReXRank dependency. tests/ is mounted into this
    # container only for the verifier step, so the agent never saw it.
    return """#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
exec /opt/verifier-venv/bin/python verify_meta_task.py
"""


def _copy_evaluator(tests_dir: Path) -> None:
    # The verifier imports `harbor_evaluator` (its filename, not `evaluator`),
    # so preserve the original module name when copying into tests/.
    evaluator_src = Path(__file__).parent / "harbor_evaluator.py"
    if evaluator_src.exists():
        (tests_dir / "harbor_evaluator.py").write_text(evaluator_src.read_text())


def _copy_verifier(tests_dir: Path) -> None:
    verifier_src = Path(__file__).parent / "verify_meta_task.py"
    if verifier_src.exists():
        (tests_dir / "verify_meta_task.py").write_text(verifier_src.read_text())


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
            for dicom_id in study["dicom_ids"]:
                rel = (
                    f"files/{group}/p{subject_id}/"
                    f"s{study['study_id']}/{dicom_id}.jpg"
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
    bootstrap_path = env_dir / "bootstrap.sh"
    bootstrap_path.write_text(_generate_bootstrap_sh())
    bootstrap_path.chmod(0o755)

    (env_dir / "Dockerfile").write_text(_generate_dockerfile())
    (env_dir / "docker-compose.yaml").write_text(
        _generate_docker_compose(task, image_root, reports_zip)
    )
    # .dockerignore at the build context root (= task dir / ..) keeps
    # tests/ and other verifier-only assets out of the image build.
    (output_dir / ".dockerignore").write_text(_generate_dockerignore())
    (workspace_dir / "README.md").write_text(_generate_workspace_readme(task))

    # NOTE: We intentionally do NOT write benchmark_tasks.json here.
    # The agent discovers everything it needs by exploring /data/patient/
    # (images + per-study report.txt) and reading /workspace/submission.json
    # for the prose instruction. Listing prior studies and target metadata
    # at generation time was leaking too much structure.

    # submission.json — minimal template for the agent to fill. Harbor
    # passes the prose instruction (instruction.md) to the codex CLI
    # directly, so we don't duplicate it here. The verifier only needs
    # task_id (to look up the answer key) and final_answer (to score).
    submission = [
        {
            "task_id": task["task_id"],
            "final_answer": "",
        }
    ]
    _write_json(workspace_dir / "submission.json", submission)

    # Tests
    tests_dir = output_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    _write_json(tests_dir / "task_answer_key.json", [answer_key])
    _copy_evaluator(tests_dir)
    _copy_verifier(tests_dir)

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


def _mimic_case_to_task(
    opaque_case_id: str,
    subject_id: str,
    target_study_id: str,
    patient_studies: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build a task dict from MIMIC raw metadata only.

    Looks up every study for ``subject_id`` in ``patient_studies``
    (output of ``build_patient_studies``), identifies the target by
    ``target_study_id``, and treats every chronologically earlier
    study for the same subject as a prior. No external corpus is
    consulted at generation time — only MIMIC's own metadata CSV.

    ``opaque_case_id`` (e.g. ``case_01``) is what the agent sees as
    task_id; subject/study IDs stay in the manifest, bind-mounted only
    into the bootstrap service.
    """
    studies = patient_studies.get(subject_id, [])
    if not studies:
        raise ValueError(f"subject_id {subject_id} not found in MIMIC metadata")
    target = next((s for s in studies if str(s["study_id"]) == target_study_id), None)
    if target is None:
        raise ValueError(
            f"target study_id {target_study_id} not found for subject {subject_id}; "
            f"available study_ids: {[str(s['study_id']) for s in studies][:10]}"
        )

    target_dt = target.get("study_datetime", "")
    priors = sorted(
        (s for s in studies
         if str(s["study_id"]) != target_study_id
         and s.get("study_datetime", "") < target_dt),
        key=lambda s: s.get("study_datetime", ""),
    )

    def _study_dict(s: dict[str, Any]) -> dict[str, Any]:
        return {
            "study_id": str(s["study_id"]),
            "study_datetime": s.get("study_datetime", ""),
            "procedure": s.get("procedure", ""),
            "views": [
                {"dicom_id": v["dicom_id"], "view_position": v.get("view_position", "")}
                for v in s.get("views", [])
            ],
        }

    history_studies = [_study_dict(p) for p in priors]
    target_study = _study_dict(target)
    target_study["given_sections"] = {}  # populated by entrypoint at runtime

    task = {
        "task_id": opaque_case_id,
        "subject_id": subject_id,
        "target_study": target_study,
        "history": history_studies,
    }
    task["instruction"] = _build_instruction(
        subject_id=subject_id,
        target=target_study,
        history=history_studies,
        given_sections={},
    )
    return task


def _write_curated_task_dir(task: dict[str, Any], output_root: Path) -> Path:
    """Write a fully self-contained task directory for one curated case.
    The directory is named with the opaque ``task_id`` (e.g. ``case_01``)
    so the host-side path and the agent's view of the task name carry
    no MIMIC identifiers."""
    out = output_root / task["task_id"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    subject_id = task["subject_id"]
    target_study_id = task["target_study"]["study_id"]

    (out / "task.toml").write_text(_generate_task_toml(task["task_id"], subject_id))
    (out / "instruction.md").write_text(_generate_instruction_md(task))

    env_dir = out / "environment"
    ws_dir = env_dir / "workspace"
    ws_dir.mkdir(parents=True, exist_ok=True)
    _write_json(env_dir / "task_manifest.json", _build_task_manifest(task))
    bootstrap = env_dir / "bootstrap.sh"
    bootstrap.write_text(_generate_bootstrap_sh())
    bootstrap.chmod(0o755)
    (env_dir / "Dockerfile").write_text(_generate_dockerfile())
    (env_dir / "docker-compose.yaml").write_text(
        _generate_docker_compose(task, DEFAULT_IMAGE_ROOT, DEFAULT_REPORTS_ZIP)
    )
    _write_json(ws_dir / "submission.json", [
        {"task_id": task["task_id"], "final_answer": ""}
    ])
    (out / ".dockerignore").write_text(_generate_dockerignore())

    tests_dir = out / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    # Answer key carries ONLY the opaque task_id + scoring metadata. Real
    # subject_id / study_id are intentionally omitted so even an
    # accidental /tests leak couldn't reveal the source corpus. Gold
    # FINDINGS/IMPRESSION come from /tests/target_report.txt at verify
    # time, not from this file.
    _write_json(tests_dir / "task_answer_key.json", [{
        "task_id": task["task_id"],
        "category": "report_generation",
        "difficulty": "hard",
    }])
    _copy_evaluator(tests_dir)
    _copy_verifier(tests_dir)
    test_sh = tests_dir / "test.sh"
    test_sh.write_text(_generate_test_script())
    test_sh.chmod(0o755)
    return out


def _build_curated(output_root: Path, purge: bool) -> None:
    """Write the ``CURATED_CASES`` task tree under output_root.

    Builds entirely from MIMIC's raw metadata.csv.gz — the curated
    (subject_id, study_id) tuples are hardcoded in ``CURATED_CASES``
    above. The ground-truth reports for those tuples were manually
    reviewed for clinical accuracy.

    Requires ``mimic-cxr-2.0.0-metadata.csv.gz`` on host (run
    ``scripts/xray_report_correction/setup.sh``). Fails loudly if missing —
    we can't build longitudinal histories without it.
    """
    output_root.mkdir(parents=True, exist_ok=True)
    if purge:
        # Sweep ALL existing per-task dirs — opaque case_NN and legacy
        # p*_s* alike — so re-running --purge gives a clean slate.
        for d in list(output_root.glob("p*_s*")) + list(output_root.glob("case_*")):
            if d.is_dir():
                shutil.rmtree(d)

    meta_path = DEFAULT_META_ROOT / "mimic-cxr-2.0.0-metadata.csv.gz"
    if not meta_path.exists():
        raise SystemExit(
            f"MIMIC metadata not found at {meta_path}.\n"
            "Run `bash scripts/xray_report_correction/setup.sh` first "
            "(downloads mimic-cxr-2.0.0-metadata.csv.gz from PhysioNet "
            "using PN_USER/PN_PASS in .env)."
        )

    print(f"Loading MIMIC metadata from {meta_path}...")
    # CURATED_CASES holds hashed (subject_id, study_id) pairs. Translate
    # back to real IDs for the duration of generation so the existing
    # MIMIC-aware logic (metadata lookup, downloads, prior extraction)
    # keeps working unchanged. The hashes go back into the committed
    # task_manifest.json / bootstrap.sh in ``_build_task_manifest`` and
    # ``_generate_bootstrap_sh``.
    translation = _load_translation_maps()
    curated_real = [
        (opaque, translation["subject"]["h2r"][s_hash], translation["study"]["h2r"][t_hash])
        for opaque, s_hash, t_hash in CURATED_CASES
    ]

    rows = load_metadata(DEFAULT_META_ROOT)
    curated_subjects = {subj for _, subj, _ in curated_real}
    rows = [r for r in rows if str(r.get("subject_id", "")) in curated_subjects]
    patient_studies = build_patient_studies(rows)
    print(f"  Loaded studies for {len(patient_studies)} patient(s).")

    print(f"Building {len(curated_real)} curated tasks under {output_root}...")
    for opaque_id, subject_id, target_study_id in curated_real:
        task = _mimic_case_to_task(
            opaque_case_id=opaque_id,
            subject_id=subject_id,
            target_study_id=target_study_id,
            patient_studies=patient_studies,
        )
        out = _write_curated_task_dir(task, output_root)
        n_priors = len(task["history"])
        n_views = len(task["target_study"]["views"])
        print(f"  ✓ {out.name}  (priors={n_priors}, target_views={n_views})")
    print("Done.")


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
    parser.add_argument(
        "--disease-stratified",
        action="store_true",
        help=(
            "Pick 14 patients (1 per CheXpert-14 category) from the EXISTING "
            "patient pool — by default, all patient dirs already present under "
            "--output-root. Use --selected-subject-ids to override the pool. "
            "Requires mimic-cxr-2.0.0-chexpert.csv.gz next to the split CSV "
            "(setup.sh downloads it). Skips full eligibility scan."
        ),
    )
    parser.add_argument(
        "--tiered-stratified",
        action="store_true",
        help=(
            "Pick a fixed 10-task severity-tiered sample over the EXISTING "
            "patient pool: 1 normal (No Finding) + 3 light (1 positive) + "
            "3 medium (2-3 positives) + 3 heavy (4+ positives), with greedy "
            "set-cover across the 12 CheXpert pathology categories. Mutually "
            "exclusive with --disease-stratified."
        ),
    )
    parser.add_argument(
        "--curated",
        action="store_true",
        help=(
            "Build the hardcoded ``CURATED_CASES`` set (10 MIMIC cases "
            "whose ground-truth FINDINGS were manually reviewed for "
            "clinical accuracy; mix of longitudinal and single-study). "
            "The (opaque_id, subject_id, target_study_id) tuples are "
            "hardcoded; the generator reads MIMIC's "
            "mimic-cxr-2.0.0-metadata.csv.gz to enumerate all priors "
            "per patient. Run setup.sh first if not already downloaded. "
            "Mutually exclusive with the other stratification flags."
        ),
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Before writing curated tasks, delete every existing dir matching p*_s* under --output-root.",
    )

    args = parser.parse_args()

    n_modes = sum([
        bool(args.disease_stratified),
        bool(args.tiered_stratified),
        bool(args.curated),
    ])
    if n_modes > 1:
        raise SystemExit(
            "--disease-stratified, --tiered-stratified, and --curated are mutually exclusive."
        )

    if args.curated:
        _build_curated(
            output_root=Path(args.output_root),
            purge=args.purge,
        )
        return

    selected_ids = None
    if args.selected_subject_ids:
        selected_ids = args.selected_subject_ids.split(",")

    if args.disease_stratified or args.tiered_stratified:
        # Determine the pool to stratify over. Default: scan output_root for
        # existing per-patient task dirs (format ``p{subject}_s{study}``).
        # The dir name already encodes both subject_id and target study_id,
        # so we don't need to re-load the giant metadata CSV.
        mode_flag = "--disease-stratified" if args.disease_stratified else "--tiered-stratified"
        out_root = Path(args.output_root)
        existing = sorted(out_root.glob("p*_s*")) if selected_ids is None else []
        pool: dict[str, str] = {}  # subject_id → target study_id
        if selected_ids is None:
            for d in existing:
                if not d.is_dir():
                    continue
                parts = d.name.split("_")
                if len(parts) != 2 or not parts[0].startswith("p") or not parts[1].startswith("s"):
                    continue
                subj = parts[0][1:]
                study = parts[1][1:]
                pool[subj] = study
            if not pool:
                raise SystemExit(
                    f"{mode_flag} expects existing patient dirs at "
                    f"{out_root}/p<subject>_s<study> (or pass --selected-subject-ids). "
                    "None found."
                )
            print(f"Stratified pool ({mode_flag}): {len(pool)} patients from {out_root}")
        else:
            # When the caller passed explicit subject_ids, we don't know
            # their target study_ids without a metadata load. Refuse rather
            # than guess — the common path is the default existing-dir scan.
            raise SystemExit(
                f"{mode_flag} + --selected-subject-ids is not supported. "
                "Drop --selected-subject-ids; the stratifier reads the pool from "
                "existing task dirs under --output-root."
            )

        labels = load_chexpert_labels(Path(args.meta_root))

        # Build a synthetic patient_studies dict so we can reuse
        # disease_stratified_sample (which expects the standard shape).
        synthetic_patient_studies = {
            subj: [{"study_id": study}] for subj, study in pool.items()
        }
        if args.tiered_stratified:
            picks = tiered_disease_stratified_sample(
                eligible=list(pool.keys()),
                patient_studies=synthetic_patient_studies,
                chexpert_labels=labels,
                n_normal=1, n_light=3, n_medium=3, n_heavy=3,
                seed=args.seed,
            )
            print(f"\nTiered picks ({len(picks)} of 10):")
        else:
            picks = disease_stratified_sample(
                eligible=list(pool.keys()),
                patient_studies=synthetic_patient_studies,
                chexpert_labels=labels,
                seed=args.seed,
            )
            print(f"\nStratified picks ({len(picks)} of {len(CHEXPERT14_LABELS)}):")
        for cat, subj in picks:
            print(f"  {cat:30s} → subject_id={subj} (study_id={pool[subj]})")
        kept_subjects = {subj for _, subj in picks}

        # In-place regenerate: re-emit only the files the new evaluator
        # cares about (instruction, env files, tests). Keep workspace/
        # benchmark_tasks.json and environment/task_manifest.json
        # untouched — those carry per-patient task data unchanged. Delete
        # patient dirs not in the kept set.
        kept_dirs: list[Path] = []
        removed = 0
        for d in existing:
            if not d.is_dir():
                continue
            parts = d.name.split("_")
            subj = parts[0][1:]
            if subj in kept_subjects:
                kept_dirs.append(d)
            else:
                import shutil as _shutil
                _shutil.rmtree(d)
                removed += 1
        print(f"\nRemoved {removed} non-selected patient dir(s).")

        # Re-emit the changed files in each kept dir.
        #
        # Source of truth, in order of preference:
        #   1. ``environment/workspace/benchmark_tasks.json`` (legacy: still
        #      carries the full task dict with target_study.given_sections).
        #      First-run regen uses this, then deletes it.
        #   2. ``environment/task_manifest.json`` (post-migration: has
        #      target_given_sections + studies). Subsequent regens use this.
        #
        # Both paths reconstruct the same ``task`` dict shape so the rest
        # of the loop is identical.
        import shutil as _shutil
        from normalization import _build_instruction  # type: ignore  # noqa: PLC0415

        def _load_task_from_dir(d: Path) -> dict[str, Any]:
            wp = d / "environment" / "workspace" / "benchmark_tasks.json"
            if wp.exists():
                return json.loads(wp.read_text())[0]
            mp = d / "environment" / "task_manifest.json"
            if not mp.exists():
                raise SystemExit(
                    f"{d}: neither benchmark_tasks.json nor task_manifest.json "
                    "found — cannot regenerate."
                )
            m = json.loads(mp.read_text())
            studies = m["studies"]
            target_sid = m["target_study_id"]
            history_studies = [s for s in studies if not s["is_target"]]
            target_study = next(s for s in studies if s["is_target"])
            def _study_dict(s: dict[str, Any]) -> dict[str, Any]:
                # Reconstruct the shape build_task_for_patient produced.
                # Accept BOTH the new minimal manifest (``dicom_ids`` flat
                # list) and the legacy one (``views`` list of dicts) so
                # mid-migration regens don't break.
                folder = s["folder"]
                # folder like "2133-10-06_00-42-28_s50051329" → derive a
                # study_datetime string when the manifest doesn't carry one
                stem = folder.rsplit("_s", 1)[0]   # "2133-10-06_00-42-28"
                date_part, _, time_part = stem.partition("_")
                derived_ts = f"{date_part} {time_part.replace('-', ':')}"
                ts = s.get("study_datetime") or derived_ts
                if "dicom_ids" in s:
                    dicom_ids = list(s["dicom_ids"])
                else:
                    dicom_ids = [v["dicom_id"] for v in s.get("views", [])]
                return {
                    "study_id": s["study_id"],
                    "study_datetime": ts,
                    "procedure": s.get("procedure", ""),
                    "views": [
                        {
                            "dicom_id": did,
                            "view_position": "",
                            "path": f"/data/patient/{folder}/{did}.jpg",
                        }
                        for did in dicom_ids
                    ],
                }
            target_dict = _study_dict(target_study)
            target_dict["given_sections"] = {}
            return {
                "task_id": f"mimic_cxr_report_{m['subject_id']}_{target_sid}",
                "subject_id": m["subject_id"],
                "target_study": target_dict,
                "history": [_study_dict(s) for s in history_studies],
            }

        # Gold FINDINGS + IMPRESSION are NOT extracted on the host side —
        # the answer key carries only the lookup keys (task_id, study_id,
        # subject_id). The verifier inside each task container fetches
        # the target report from PhysioNet on demand using PN_USER /
        # PN_PASS forwarded via docker-compose. This keeps the repo and
        # generated tasks/ tree free of credentialed MIMIC text.

        for d in kept_dirs:
            task = _load_task_from_dir(d)
            # Rebuild the embedded instruction string with the new
            # exploration-style wording.
            task["instruction"] = _build_instruction(
                subject_id=task["subject_id"],
                target=task["target_study"],
                history=task.get("history", []),
                given_sections=task["target_study"].get("given_sections", {}),
            )
            # Refresh workspace/submission.json — minimal template; the
            # prose instruction reaches the agent via Harbor's
            # instruction.md → codex-CLI-prompt pipeline, not via this file.
            sub_path = d / "environment" / "workspace" / "submission.json"
            _write_json(
                sub_path,
                [
                    {
                        "task_id": task["task_id"],
                        "final_answer": "",
                    }
                ],
            )
            # Instruction.md — single source of truth (just emits the
            # submission.json instruction prose verbatim).
            (d / "instruction.md").write_text(_generate_instruction_md(task))
            # Rebuild the task manifest with target_given_sections so the
            # entrypoint can write the partial report.txt at runtime.
            env_dir = d / "environment"
            _write_json(env_dir / "task_manifest.json", _build_task_manifest(task))
            # Remove the now-stale agent-visible files left over from older
            # generations.
            legacy_bm = d / "environment" / "workspace" / "benchmark_tasks.json"
            if legacy_bm.exists():
                legacy_bm.unlink()
            ws_readme = d / "environment" / "workspace" / "README.md"
            if ws_readme.exists():
                ws_readme.unlink()
            # Environment files (Dockerfile + bootstrap.sh + compose).
            env_dir = d / "environment"
            (env_dir / "Dockerfile").write_text(_generate_dockerfile())
            bootstrap = env_dir / "bootstrap.sh"
            bootstrap.write_text(_generate_bootstrap_sh())
            bootstrap.chmod(0o755)
            # Remove any stale entrypoint.sh from the old single-service
            # design so the new layout is fully clean.
            stale_entry = env_dir / "entrypoint.sh"
            if stale_entry.exists():
                stale_entry.unlink()
            (env_dir / "docker-compose.yaml").write_text(
                _generate_docker_compose(task, Path(args.image_root), Path(args.reports_zip))
            )
            # .dockerignore at the task root keeps tests/ out of the
            # build context. The build context is ``..`` (the task dir).
            (d / ".dockerignore").write_text(_generate_dockerignore())
            # Tests dir: new answer_key (with gold FINDINGS + IMPRESSION
            # baked in) + harbor_evaluator + verify_meta_task + test.sh.
            # The gold text is extracted from the locally-downloaded MIMIC
            # reports zip — NEVER from the public ReXRank JSON. The
            # answer_key file is gitignored so the gold doesn't leak via
            # version control.
            tests_dir = d / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            # Drop the old f1chexbert labeler if present — no longer used.
            for old in ("chexbert_labeler.py", "evaluator.py"):
                p = tests_dir / old
                if p.exists():
                    p.unlink()
            # Answer key carries only lookup keys; the verifier bootstraps
            # gold FINDINGS + IMPRESSION from PhysioNet at run time.
            target_sid = str(task["target_study"]["study_id"])
            answer_key = {
                "task_id": task["task_id"],
                "category": "report_generation",
                "difficulty": "hard",
                "study_id": target_sid,
                "subject_id": str(task["subject_id"]),
            }
            _write_json(tests_dir / "task_answer_key.json", [answer_key])
            _copy_evaluator(tests_dir)
            _copy_verifier(tests_dir)
            test_sh = tests_dir / "test.sh"
            test_sh.write_text(_generate_test_script())
            test_sh.chmod(0o755)
        print(f"Re-emitted {len(kept_dirs)} kept task dir(s).")
        return  # Skip the full regen-from-metadata path below.

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
