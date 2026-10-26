#!/usr/bin/env python3
"""Bootstrap-only staging for one mri_qa task (five exams).

Runs inside the per-trial ``bootstrap`` compose service, never inside the
agent's ``main`` container. Given the bind-mounted task manifest it:

  1. Downloads each exam's three MRNet series from Redivis on a cache miss
     (``REDIVIS_API_TOKEN`` from the repo-root ``.env`` via ``env_file``) and
     verifies every array against the manifest's pinned byte count and MD5.
  2. Downloads the public validation label tables on a cache miss and checks
     them against the manifest's pinned canonical SHA-256 digests, so a
     changed source table fails loudly instead of silently shifting gold.
  3. Derives the ACL and meniscus gold for every exam at run time from those
     tables and writes ``/tests/gold.json`` + ``/tests/data_verification.json``
     (gitignored on the host; Harbor mounts ``tests/`` into main only when the
     verifier runs).
  4. Stages the agent-visible files into the shared named volume, one
     ``exam_<k>/`` directory per exam holding exactly the three MRNet arrays,
     re-serialised to drop the source filename but otherwise byte-for-byte
     the released pixels. No derived images are provided; the agent renders
     what it needs from the arrays.

The manifest never carries answers; ``stage`` refuses to run if it does.
"""

from __future__ import annotations

import argparse
import base64
import csv
import fcntl
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

KEYS = ("abnormal", "acl", "meniscus")  # source label tables
ANSWER_KEYS = ("acl", "meniscus")  # questions asked
PLANES = ("axial", "coronal", "sagittal")
LABEL_HEADER = ["_1130", "_0"]
LABEL_EXAM_IDS = {f"{i:04d}" for i in range(1131, 1250)}


def log(message: str) -> None:
    print(f"[bootstrap] {message}", flush=True)


@contextmanager
def locked(lock_path: Path):
    """Exclusive flock so concurrent trials share one cache without racing.

    The container runs as root while maintainers stage on the host as a normal
    user, so the lock directory and files are made world-writable. No sticky
    bit: with fs.protected_regular set, even root cannot O_CREAT-open another
    user's file inside a sticky world-writable directory.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    for path, mode in ((lock_path.parent, 0o777), (lock_path, 0o666)):
        try:
            if path == lock_path:
                path.touch(exist_ok=True)
            os.chmod(path, mode)
        except OSError:
            pass
    with lock_path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def require_token() -> None:
    if not os.environ.get("REDIVIS_API_TOKEN", "").strip():
        sys.stderr.write(
            "[bootstrap] REDIVIS_API_TOKEN is not set and the MRI cache is cold.\n"
            "  Request access to Stanford AIMI MRNet at\n"
            "  https://stanford.redivis.com/datasets/4a2c-4cpkzrn2c, create a token at\n"
            "  https://redivis.com/workspace/settings/tokens, and add\n"
            "  REDIVIS_API_TOKEN=... to the repo-root .env file.\n"
        )
        sys.exit(2)


def redivis_dataset(name: str):
    require_token()
    import redivis  # heavy import; bootstrap image only

    return redivis.dataset(name)


def freeze(path: Path) -> None:
    try:
        path.chmod(0o444)
    except OSError:
        pass


def parse_labels(text: str) -> tuple[dict[str, int], str]:
    """Return ``{exam_id: 0|1}`` and a canonical digest independent of row order."""
    rows = list(csv.reader(text.splitlines()))
    if not rows or rows[0] != LABEL_HEADER:
        raise ValueError(f"Unexpected source label schema: {rows[:1]}")
    labels: dict[str, int] = {}
    for row in rows[1:]:
        if len(row) != 2 or row[1] not in ("0", "1"):
            raise ValueError("Nonbinary or malformed source label")
        case = f"{int(row[0]):04d}"
        if case in labels:
            raise ValueError(f"Duplicate exam ID {case}")
        labels[case] = int(row[1])
    if set(labels) != LABEL_EXAM_IDS:
        raise ValueError("Unexpected public validation exam IDs")
    canonical = "\n".join(f"{k},{v}" for k, v in sorted(labels.items()))
    return labels, hashlib.sha256(canonical.encode()).hexdigest()


def fetch_label_table(manifest: dict, key: str, cache: Path) -> dict[str, int]:
    spec = manifest["label_tables"][key]
    dest = cache / "labels" / f"{spec['table'].split(':')[0]}.csv"
    with locked(cache / ".bootstrap.locks" / f"labels_{key}.lock"):
        if not dest.exists():
            log(f"cache miss: downloading label table {spec['table']}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp = dest.with_name(f".partial-{dest.name}")
            written = redivis_dataset(manifest["dataset"]).table(spec["table"]).download(
                str(temp), format="csv", overwrite=True, progress=False
            )
            if [str(temp)] != [str(p) for p in written]:
                raise RuntimeError(f"Unexpected download path for {spec['table']}: {written}")
            temp.replace(dest)
            freeze(dest)
        else:
            log(f"cache hit: {dest}")
    labels, digest = parse_labels(dest.read_text())
    if digest != spec["canonical_sha256"]:
        raise ValueError(
            f"Label table {spec['table']} differs from the pinned snapshot "
            f"({digest} != {spec['canonical_sha256']}); refusing to derive gold"
        )
    return labels


def fetch_array(manifest: dict, entry: dict, cache: Path) -> Path:
    dest = cache / entry["file_name"]
    with locked(cache / ".bootstrap.locks" / f"{entry['file_name'].replace('/', '_')}.lock"):
        if not dest.exists():
            log(f"cache miss: downloading {entry['file_name']}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp = dest.with_name(f".partial-{dest.name}")
            redivis_dataset(manifest["dataset"]).table(manifest["image_table"]).file(
                entry["file_name"]
            ).download(str(temp), overwrite=True, progress=False)
            temp.replace(dest)
            freeze(dest)
        else:
            log(f"cache hit: {dest}")
    raw = dest.read_bytes()
    md5 = base64.b64encode(hashlib.md5(raw).digest()).decode()
    if len(raw) != int(entry["size"]) or md5 != entry["md5_hash"]:
        raise ValueError(f"MRI source size/checksum mismatch: {entry['file_name']}")
    return dest


def stage_exam(manifest: dict, exam: dict, cache: Path, out: Path) -> dict:
    import numpy as np

    out.mkdir(parents=True, exist_ok=True)
    verification = {}
    for plane in PLANES:
        entry = exam["files"][plane]
        if entry["file_name"] != f"{plane}/{exam['source_exam_id']}.npy":
            raise ValueError("MRI plane/exam identity mismatch")
        source = fetch_array(manifest, entry, cache)
        raw = source.read_bytes()
        array = np.load(source, allow_pickle=False)
        if (
            array.dtype != np.uint8
            or array.ndim != 3
            or array.shape[1:] != (256, 256)
            or array.shape[0] < 1
            or array.max() == array.min()
        ):
            raise ValueError(f"Invalid MRI array: {entry['file_name']}")
        # Re-serialise to drop source filenames; keep every pixel and slice.
        np.save(out / f"{plane}.npy", array, allow_pickle=False)
        if not np.array_equal(np.load(out / f"{plane}.npy"), array):
            raise ValueError("Staged pixels differ from source")
        verification[plane] = {
            "source_md5_matches": True,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "staged_pixels_equal": True,
        }
    return verification


def stage(manifest_path: Path, cache: Path, workspace: Path, tests: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    if "labels" in manifest or "answers" in manifest or any(
        "labels" in e or "answers" in e for e in manifest["exams"]
    ):
        raise ValueError("Task manifest must not carry answers; gold is derived at run time")
    exams = manifest["exams"]
    slots = [e["slot"] for e in exams]
    ids = [e["source_exam_id"] for e in exams]
    if len(set(slots)) != len(slots) or len(set(ids)) != len(ids):
        raise ValueError("Exam slots and source IDs must be distinct")
    cache.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    tests.mkdir(parents=True, exist_ok=True)

    # Arrays first: a corrupt cache fails closed before any label handling.
    verification = {e["slot"]: stage_exam(manifest, e, cache, workspace / e["slot"]) for e in exams}

    # Gold: derived from the pinned public label tables, never from the repo.
    tables = {k: fetch_label_table(manifest, k, cache) for k in KEYS}
    answers = {}
    for e in exams:
        row = {k: tables[k][e["source_exam_id"]] for k in KEYS}
        if not row["abnormal"] and (row["acl"] or row["meniscus"]):
            raise ValueError(f"Inconsistent source labels for exam {e['source_exam_id']}")
        answers[e["slot"]] = {k: row[k] for k in ANSWER_KEYS}
    gold = {
        "task_id": manifest["task_id"],
        "answers": answers,
        "source_exam_ids": {e["slot"]: e["source_exam_id"] for e in exams},
        "dataset": manifest["dataset"],
    }
    (tests / "gold.json").write_text(json.dumps(gold, indent=2) + "\n")
    (tests / "data_verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    log(f"{manifest['task_id']}: verified {3 * len(exams)} source checksums, derived gold, staged {len(exams)} exams (arrays only)")
    return gold


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("/opt/task_manifest.json"))
    parser.add_argument("--cache", type=Path, default=Path("/data/_cache"))
    parser.add_argument("--workspace", type=Path, default=Path("/workspace/mri"))
    parser.add_argument("--tests", type=Path, default=Path("/tests"))
    args = parser.parse_args()
    stage(args.manifest, args.cache, args.workspace, args.tests)


if __name__ == "__main__":
    main()
