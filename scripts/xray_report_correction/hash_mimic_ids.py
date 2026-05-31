#!/usr/bin/env python3
"""Hash MIMIC-CXR subject/study/dicom IDs for opaque reference.

Reads ``mimic-cxr-2.0.0-metadata.csv.gz`` (which enumerates every (subject,
study, dicom) triple in the MIMIC-CXR-JPG release) and writes a flat CSV
that maps each real ID to a stable 16-char hex hash. The CSV lives in the
gitignored assets dir; the rest of the pipeline (generator + bootstrap)
references IDs only by their hash, so no MIMIC IDs end up in committed
repo files.

The hash function is ``sha256(SALT + str(real_id))[:16]``. The salt is
fixed in this script (not a secret) so any machine that runs this script
against the same MIMIC release produces the same translation table.

Output CSV columns: ``kind,real,hash``
  * ``kind`` is one of ``subject``, ``study``, ``dicom``
  * ``real`` is the original ID (string)
  * ``hash`` is 16 hex chars

Usage:
    uv run python scripts/xray_report_correction/hash_mimic_ids.py
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import sys
from pathlib import Path

# Fixed salt — not a secret. Bump the version suffix only if you want
# to deliberately invalidate the existing translation table.
SALT = "medcli-xray-report-correction-v1"

# Truncate the hash to keep the IDs readable in code/JSON. 16 hex chars
# = 64 bits of entropy, well over what's needed to avoid collisions on
# MIMIC-CXR (~64k subjects, ~377k studies, ~377k dicoms).
HASH_LEN = 16

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "scripts" / "xray_report_correction" / "assets"
METADATA_CSV = ASSETS_DIR / "mimic-cxr-jpg" / "2.1.0" / "mimic-cxr-2.0.0-metadata.csv.gz"
# Put the translation CSV inside the JPG dataset dir so it's automatically
# available to bootstrap via the existing ``/data/_src/jpg_root`` mount —
# no extra bind mount required. Bootstrap will regenerate this file on
# the fly if it's missing on the host.
TRANSLATION_CSV = ASSETS_DIR / "mimic-cxr-jpg" / "2.1.0" / "id_translation.csv"


def hash_id(real: str) -> str:
    return hashlib.sha256(f"{SALT}|{real}".encode()).hexdigest()[:HASH_LEN]


def _ensure_metadata_csv() -> None:
    """Download the MIMIC metadata CSV if it isn't on disk yet.

    Calls into ``setup.sh`` for the wget logic (which already serializes
    concurrent invocations with flock and skips files that already
    exist). Requires PN_USER / PN_PASS in the host env.
    """
    if METADATA_CSV.is_file():
        return
    import os
    import subprocess
    if not os.environ.get("PN_USER") or not os.environ.get("PN_PASS"):
        raise SystemExit(
            f"MIMIC metadata not found at {METADATA_CSV} and PN_USER / "
            f"PN_PASS are not set in the environment. Export PhysioNet "
            f"credentials (e.g. ``set -a && . ./.env && set +a``) and re-run."
        )
    setup_sh = REPO_ROOT / "scripts" / "xray_report_correction" / "setup.sh"
    print(
        f"[hash_mimic_ids] {METADATA_CSV.name} missing — "
        f"running setup.sh to download from PhysioNet (one-time)..."
    )
    subprocess.run(["bash", str(setup_sh)], check=True)


def main() -> int:
    _ensure_metadata_csv()

    print(f"Reading {METADATA_CSV} ...")
    subjects: set[str] = set()
    studies: set[str] = set()
    dicoms: set[str] = set()
    with gzip.open(METADATA_CSV, "rt", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if s := row.get("subject_id"):
                subjects.add(s)
            if s := row.get("study_id"):
                studies.add(s)
            if s := row.get("dicom_id"):
                dicoms.add(s)

    print(
        f"  subjects: {len(subjects):>7,}\n"
        f"  studies:  {len(studies):>7,}\n"
        f"  dicoms:   {len(dicoms):>7,}"
    )

    TRANSLATION_CSV.parent.mkdir(parents=True, exist_ok=True)
    with TRANSLATION_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "real", "hash"])
        for s in sorted(subjects):
            w.writerow(["subject", s, hash_id(s)])
        for s in sorted(studies):
            w.writerow(["study", s, hash_id(s)])
        for s in sorted(dicoms):
            w.writerow(["dicom", s, hash_id(s)])

    print(f"Wrote {TRANSLATION_CSV}  ({sum(map(len,(subjects,studies,dicoms))):,} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
