"""One-time host-side downloader for all EHRSHOT benchmark assets.

EHRSHOT is gated on Redivis (Stanford SHAH lab dataset). This script downloads
**every EHRSHOT-related artifact MedCLI uses** (the canonical
``EHRSHOT_ASSETS.zip`` bundle: raw OMOP events, splits, per-task labels,
features, published baseline AUROCs) and validates the on-disk manifest. It
is meant to be run **once on the host** before invoking
``generate_harbor_tasks.py``; container code never authenticates to Redivis.

Authentication uses a long-lived **Redivis API token**, NOT the OAuth browser
flow. Set ``REDIVIS_API_TOKEN`` (or persist it in
``~/.config/redivis/config``) before running this script. Without a token the
script exits non-zero with the access URL in the message.

Usage:

    # one-time per host
    export REDIVIS_API_TOKEN="rdv_xxxxxxxxxxxx"
    uv run python scripts/ehrshot/download.py

By default everything lands inside the repo at
``scripts/ehrshot/assets/EHRSHOT_ASSETS/`` (gitignored — see
``.gitignore``). Override with ``--assets-dir`` or ``EHRSHOT_ASSETS_DIR`` if
you'd rather stage outside the repo (e.g. on shared scratch).

Re-running on a populated cache is idempotent: the script validates the
manifest and exits 0 without any network access if everything is already
present.

For Phase 1 of the EHRSHOT integration we only need the assets for the
``guo_icu`` task (and the shared ``data/`` + ``splits/`` directories). The
manifest checked here is the *Phase-1 minimal* set; the complete
all-15-tasks manifest is documented in the ExecPlan and will be tightened in
Phase 2.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path


REDIVIS_TABLE_REF = "shahlab.ehrshot:53gc:v3_0.files:4avd"
REDIVIS_FILE_NAME = "EHRSHOT_ASSETS.zip"
ACCESS_URL = "https://redivis.com/datasets/53gc-8rhx41kgt"

# Repo-relative default: keep the bulk bundle under the benchmark's own
# ``scripts/ehrshot/assets/`` directory so contributors don't have to chase a
# /mnt path on shared infra. The directory is gitignored except for the
# committed ``task_configs.yaml`` (see .gitignore).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ASSETS_ROOT = REPO_ROOT / "scripts" / "ehrshot" / "assets" / "EHRSHOT_ASSETS"


def default_assets_dir() -> Path:
    """Resolve the on-disk root for ``EHRSHOT_ASSETS/``.

    Order of preference:
      1. ``EHRSHOT_ASSETS_DIR`` environment variable (if set and non-empty).
      2. ``scripts/ehrshot/assets/EHRSHOT_ASSETS/`` inside the repo (default).

    Either is acceptable; the directory may be missing — this script creates
    it. The full bundle is ~10 GB; choose a path with enough disk headroom.
    """
    env = os.environ.get("EHRSHOT_ASSETS_DIR", "").strip()
    if env:
        return Path(env)
    return DEFAULT_ASSETS_ROOT


# Phase-1 minimal manifest — files we need for the guo_icu starter task.
# Phase 2 expands this when the other 14 tasks come online.
PHASE1_REQUIRED_FILES = (
    "data/ehrshot.csv",
    "splits/person_id_map.csv",
    "benchmark/guo_icu/labeled_patients.csv",
    "benchmark/guo_icu/all_shots_data.json",
    "results/guo_icu/all_results.csv",
)
PHASE1_REQUIRED_DIRS = (
    "features",  # contains count_features.pkl + clmbr_features.pkl; we let the
                 # task generator pick what it actually needs at slice time.
)


def _read_token() -> str | None:
    """Token-resolution order matches the redivis package: env first, then
    ``~/.config/redivis/config``. Returns None if neither is populated.
    """
    tok = os.environ.get("REDIVIS_API_TOKEN", "").strip()
    if tok:
        return tok
    cfg = Path.home() / ".config" / "redivis" / "config"
    if cfg.is_file():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("REDIVIS_API_TOKEN") and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def _validate_manifest(root: Path) -> tuple[bool, list[str]]:
    """Return (ok, missing_paths). ``ok`` is True iff every required file +
    directory in PHASE1_REQUIRED_FILES / PHASE1_REQUIRED_DIRS is present and
    non-empty.
    """
    missing: list[str] = []
    for rel in PHASE1_REQUIRED_FILES:
        p = root / rel
        if not p.is_file() or p.stat().st_size == 0:
            missing.append(rel)
    for rel in PHASE1_REQUIRED_DIRS:
        p = root / rel
        if not p.is_dir() or not any(p.iterdir()):
            missing.append(rel + "/  (directory)")
    return (not missing, missing)


def _download_and_extract(token: str, dest_root: Path) -> None:
    """Pull EHRSHOT_ASSETS.zip from Redivis and extract into ``dest_root``.

    The redivis-python package writes the tar/zip to a destination path of our
    choosing. We extract in-place and remove the zip on success.
    """
    try:
        import redivis  # type: ignore[import-not-found]
    except ImportError as exc:
        print(
            "[ehrshot-download] The 'redivis' Python package is not installed.\n"
            "  Run `uv add redivis` from the repo root and re-run this script.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    # Some versions of redivis read the token at table-resolution time, others
    # at download time. Set it both via env (already in os.environ if the
    # caller exported it) and programmatically when the API allows.
    os.environ.setdefault("REDIVIS_API_TOKEN", token)
    if hasattr(redivis, "set_api_token"):
        try:
            redivis.set_api_token(token)
        except Exception:  # noqa: BLE001 — best-effort; env var still works
            pass

    dest_root.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"[ehrshot-download] resolving {REDIVIS_TABLE_REF} -> {REDIVIS_FILE_NAME}",
        file=sys.stderr,
    )
    table = redivis.table(REDIVIS_TABLE_REF)
    redivis_file = table.file(REDIVIS_FILE_NAME)

    zip_path = dest_root.parent / REDIVIS_FILE_NAME
    print(
        f"[ehrshot-download] downloading {REDIVIS_FILE_NAME} (~10 GB) -> {zip_path}",
        file=sys.stderr,
    )
    redivis_file.download(str(zip_path.parent), overwrite=True)

    if not zip_path.is_file() or zip_path.stat().st_size == 0:
        raise RuntimeError(
            f"redivis download did not produce a non-empty {zip_path}"
        )

    print(f"[ehrshot-download] extracting {zip_path} -> {dest_root.parent}", file=sys.stderr)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest_root.parent)

    # The zip is expected to extract a top-level EHRSHOT_ASSETS/ dir; if the
    # caller picked a different ``dest_root`` name, normalize.
    inner = dest_root.parent / "EHRSHOT_ASSETS"
    if inner.is_dir() and inner != dest_root:
        if dest_root.exists():
            shutil.rmtree(dest_root)
        inner.rename(dest_root)

    zip_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=default_assets_dir(),
        help="Where to extract EHRSHOT_ASSETS/ (default: %(default)s).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the cache is already populated and validates.",
    )
    args = parser.parse_args(argv)

    dest = args.assets_dir
    if not args.force and dest.is_dir():
        ok, missing = _validate_manifest(dest)
        if ok:
            print(
                f"[ehrshot-download] cache OK: {dest}\n"
                "  Phase-1 manifest validates; nothing to download.",
                file=sys.stderr,
            )
            return 0
        print(
            f"[ehrshot-download] {dest} exists but the Phase-1 manifest is incomplete.\n"
            f"  Missing: {missing}\n"
            "  Re-running download to fill the gaps...",
            file=sys.stderr,
        )

    token = _read_token()
    if token is None:
        print(
            "[ehrshot-download] No Redivis API token found.\n"
            f"  1. Accept the EHRSHOT data-use agreement: {ACCESS_URL}\n"
            "  2. Generate a Redivis API token (Account -> API tokens) with read\n"
            "     scope on the shahlab.ehrshot dataset.\n"
            "  3. Export REDIVIS_API_TOKEN=\"rdv_...\" and re-run this script.\n"
            "     (Or persist the token in ~/.config/redivis/config.)",
            file=sys.stderr,
        )
        return 2

    _download_and_extract(token, dest)

    ok, missing = _validate_manifest(dest)
    if not ok:
        print(
            f"[ehrshot-download] FAILED: download completed but manifest is incomplete.\n"
            f"  Missing: {missing}\n"
            f"  This usually means the upstream Redivis bundle layout has changed.\n"
            f"  Inspect {dest} and update the manifest in scripts/ehrshot/download.py.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[ehrshot-download] OK: bundle at {dest} validates against the Phase-1 manifest",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
