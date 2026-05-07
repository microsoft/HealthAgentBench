"""Pull a per-topic clinical-trial corpus from the upstream zip snapshot.

This script is invoked in two contexts:

1. **Host-side, by ``generate_harbor_tasks.py``** to pre-stage the
   judged-pool XMLs into ``scripts/clinical_trial_matching/assets/raw_cache/``
   so that subsequent ``harbor run`` invocations are offline-fast.

2. **Container-side, by the per-task ``entrypoint.sh``** to fill any gaps
   in the host cache (mounted at ``/data/_cache``) when the generator was
   not pre-run, or when the cache was cleared. The host mount is shared
   across concurrent task containers; the entrypoint holds a per-topic
   ``flock`` so two containers for the same topic do not race writing the
   same NCT files.

Inputs:

- ``--ids <path>``           one NCT ID per line (~500 per topic).
- ``--out <dir>``             agent-visible output dir (e.g.
                              ``/workspace/data/trials``).
- ``--cache-dir <dir>``       optional host-mounted cache. If a NCT is
                              already in cache, copy it to ``--out`` and
                              skip the network. Newly downloaded NCTs are
                              written to cache **and** to ``--out``, then
                              ``chmod a-w``-marked so the cache copy
                              cannot be mutated later.
- ``--user-agent``            HTTP User-Agent header (the upstream server
                              returns HTTP 406 to clients with the
                              ``requests`` stdlib default UA).

Output: writes ``<NCT>.xml`` files into ``--out`` (and into ``--cache-dir``
if provided). Exits non-zero if any requested NCT could not be located in
any zip part.
"""

from __future__ import annotations

import argparse
import shutil
import stat
import sys
import time
from pathlib import Path

from remotezip import RemoteZip, RemoteIOError


# 5 zip parts hosting the April 27, 2021 ClinicalTrials.gov snapshot.
DEFAULT_ZIP_URLS = [
    "https://www.trec-cds.org/2021_data/ClinicalTrials.2021-04-27.part1.zip",
    "https://www.trec-cds.org/2021_data/ClinicalTrials.2021-04-27.part2.zip",
    "https://www.trec-cds.org/2021_data/ClinicalTrials.2021-04-27.part3.zip",
    "https://www.trec-cds.org/2021_data/ClinicalTrials.2021-04-27.part4.zip",
    "https://www.trec-cds.org/2021_data/ClinicalTrials.2021-04-27.part5.zip",
]


def _wanted_filename_predicate(wanted: set[str]):
    """Return a function that decides whether a zip entry path is wanted.

    Internal layout: ``ClinicalTrials.2021-04-27.partN/NCT0000xxxx/<NCT>.xml``.
    """
    def _accept(name: str) -> bool:
        if not name.endswith(".xml"):
            return False
        nct = name.rsplit("/", 1)[-1][:-4]
        return nct in wanted
    return _accept


def _read_only(path: Path) -> None:
    """Set ``a-w`` (chmod 0444) on a regular file. Tolerant to errors."""
    try:
        cur = path.stat().st_mode & 0o777
        path.chmod(cur & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    except OSError:
        pass


def _file_lock(lock_path: Path):
    """Return a context manager that holds an exclusive flock on
    ``lock_path``. Falls back to a no-op if ``filelock`` is not installed.
    """
    try:
        from filelock import FileLock as _FileLock
    except ImportError:
        from contextlib import nullcontext
        return nullcontext()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    return _FileLock(str(lock_path), timeout=300)


def fetch_from_zip(
    url: str,
    wanted: set[str],
    out_dir: Path,
    user_agent: str,
    cache_dir: Path | None = None,
    retries: int = 3,
    backoff_seconds: float = 5.0,
) -> set[str]:
    """Download specific NCT XMLs from one upstream zip via range requests.

    Returns the set of NCT IDs successfully extracted. If ``cache_dir`` is
    supplied, files are written there as well (with per-NCT flock + chmod
    a-w to mark the cache copy read-only).
    """
    if not wanted:
        return set()

    headers = {"User-Agent": user_agent}
    extracted: set[str] = set()
    last_err: Exception | None = None
    accept = _wanted_filename_predicate(wanted)

    for attempt in range(retries):
        try:
            with RemoteZip(url, headers=headers) as z:
                names = z.namelist()
                hits = [n for n in names if accept(n)]
                for entry in hits:
                    nct = entry.rsplit("/", 1)[-1][:-4]
                    if nct in extracted:
                        continue
                    with z.open(entry) as f:
                        data = f.read()
                    out_path = out_dir / f"{nct}.xml"
                    out_path.write_bytes(data)
                    if cache_dir is not None:
                        cache_path = cache_dir / f"{nct}.xml"
                        with _file_lock(cache_dir / ".locks" / f"{nct}.lock"):
                            # Re-check after taking the lock — another
                            # process may have populated this file.
                            if not cache_path.exists() or cache_path.stat().st_size == 0:
                                cache_path.write_bytes(data)
                            _read_only(cache_path)
                    extracted.add(nct)
            return extracted
        except (RemoteIOError, OSError, RuntimeError) as exc:
            last_err = exc
            if attempt < retries - 1:
                print(
                    f"[fetch_trials] {url}: attempt {attempt + 1} failed "
                    f"({exc!r}); retrying in {backoff_seconds}s",
                    file=sys.stderr,
                )
                time.sleep(backoff_seconds)
                backoff_seconds *= 1.5
                continue
    raise RuntimeError(
        f"failed to fetch from {url} after {retries} attempts: {last_err}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Optional host-mounted cache dir. Files present here are reused "
             "(no network); newly downloaded files are written here too.",
    )
    parser.add_argument(
        "--user-agent",
        default="clinical_trial_matching/1.0 (medcli benchmark)",
        help="HTTP User-Agent header. Upstream returns 406 to empty UA.",
    )
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--backoff-seconds", type=float, default=5.0)
    parser.add_argument(
        "--zip-urls",
        nargs="+",
        default=DEFAULT_ZIP_URLS,
        help="Override the upstream zip URLs (testing).",
    )
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    if args.cache_dir is not None:
        args.cache_dir.mkdir(parents=True, exist_ok=True)

    wanted: set[str] = set()
    for line in args.ids.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            wanted.add(line)
    if not wanted:
        print("[fetch_trials] no NCT IDs to fetch", file=sys.stderr)
        return 0
    print(f"[fetch_trials] wanted {len(wanted)} NCT IDs", file=sys.stderr)

    # Cache hits: copy cache -> out, drop from wanted set.
    cache_hits: set[str] = set()
    if args.cache_dir is not None:
        for nct in list(wanted):
            src = args.cache_dir / f"{nct}.xml"
            if src.is_file() and src.stat().st_size > 0:
                dst = args.out / f"{nct}.xml"
                shutil.copyfile(src, dst)
                cache_hits.add(nct)
        wanted -= cache_hits
        print(
            f"[fetch_trials] cache hits: {len(cache_hits)} "
            f"(now wanted={len(wanted)})",
            file=sys.stderr,
        )

    # Network: extract remaining from upstream zip parts (range requests).
    extracted: set[str] = set()
    for url in args.zip_urls:
        remaining = wanted - extracted
        if not remaining:
            break
        t0 = time.time()
        got = fetch_from_zip(
            url,
            remaining,
            args.out,
            args.user_agent,
            cache_dir=args.cache_dir,
            retries=args.retries,
            backoff_seconds=args.backoff_seconds,
        )
        extracted |= got
        print(
            f"[fetch_trials] {url.rsplit('/', 1)[-1]}: extracted {len(got)} "
            f"({len(extracted)}/{len(wanted)}) in {time.time() - t0:.1f}s",
            file=sys.stderr,
        )

    missing = wanted - extracted
    if missing:
        miss_path = args.out.parent / "missing_ncts.txt"
        miss_path.write_text("\n".join(sorted(missing)) + "\n")
        print(
            f"[fetch_trials] FAILED: {len(missing)} NCT IDs not found "
            f"in any zip part. See {miss_path}",
            file=sys.stderr,
        )
        return 2

    total = len(cache_hits) + len(extracted)
    print(
        f"[fetch_trials] OK: {total} XMLs in {args.out} "
        f"(cache hits: {len(cache_hits)}, downloaded: {len(extracted)})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
