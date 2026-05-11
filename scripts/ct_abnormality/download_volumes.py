"""Download the 10 manifest-pinned CT-RATE volumes into the host cache.

Reads `scripts/ct_abnormality/assets/manifest.yaml`, resolves each volume to its
Hugging Face path (`dataset/valid_fixed/<patient>/<study>/<volume>.nii.gz`),
and downloads it into `scripts/ct_abnormality/assets/raw_cache/<volume_name>.nii.gz`.
The cache directory is gitignored.

Auth: requires a Hugging Face token with read access to
`ibrahimhamamci/CT-RATE` (the dataset is OpenRAIL-gated). The token is read
from, in priority order:

  1. The `HF_TOKEN` environment variable.
  2. `~/.cache/huggingface/token` (the default cache location for
     `huggingface-cli login`).

If neither is found, the script prints the access URL and exits non-zero.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml


CT_RATE_ACCESS_URL = "https://huggingface.co/datasets/ibrahimhamamci/CT-RATE"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = REPO_ROOT / "scripts" / "ct_abnormality" / "assets"
MANIFEST_PATH = ASSETS_DIR / "manifest.yaml"
RAW_CACHE_DIR = ASSETS_DIR / "raw_cache"


def _read_token() -> str | None:
    tok = os.environ.get("HF_TOKEN", "").strip()
    if tok:
        return tok
    cached = Path.home() / ".cache" / "huggingface" / "token"
    if cached.is_file():
        text = cached.read_text(encoding="utf-8").strip()
        if text:
            return text
    return None


def _hf_path_for(volume_name: str, hf_split_root: str) -> str:
    """Resolve a volume file name to its repo-relative HF path.

    CT-RATE volume names follow the pattern ``valid_<patient>_<scan>_<index>.nii.gz``.
    Example: ``valid_670_a_1.nii.gz`` → patient dir ``valid_670``, study dir
    ``valid_670_a``, file ``valid_670_a_1.nii.gz``. The hierarchy is documented
    on the dataset's HF page.
    """
    stem = volume_name[: -len(".nii.gz")]
    parts = stem.split("_")
    if len(parts) < 4:
        raise ValueError(f"Cannot parse CT-RATE volume name: {volume_name!r}")
    patient = "_".join(parts[:2])  # e.g. "valid_670"
    study = "_".join(parts[:3])  # e.g. "valid_670_a"
    return f"{hf_split_root}/{patient}/{study}/{volume_name}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help="Path to manifest.yaml (default: %(default)s).",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=RAW_CACHE_DIR,
        help="Output cache directory (default: %(default)s).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download volumes even if a non-empty cache file already exists.",
    )
    args = parser.parse_args(argv)

    token = _read_token()
    if token is None:
        print(
            "[ct_abnormality] No Hugging Face token found.\n"
            "  Set HF_TOKEN or run `huggingface-cli login` after accepting the\n"
            f"  CT-RATE access agreement at {CT_RATE_ACCESS_URL}.",
            file=sys.stderr,
        )
        return 2

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    repo_id = manifest["hf_repo"]
    split_root = manifest["hf_split_root"]
    volumes = manifest["volumes"]

    args.cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print(
            "[ct_abnormality] huggingface_hub is not installed. "
            "Run `uv add huggingface_hub` from the repo root.",
            file=sys.stderr,
        )
        return 2

    n_total = len(volumes)
    n_skipped = 0
    n_downloaded = 0
    for entry in volumes:
        volume_name = entry["volume_name"]
        out_path = args.cache_dir / volume_name
        # Treat broken symlinks (left from earlier failed runs) as missing.
        if out_path.is_symlink() and not out_path.exists():
            out_path.unlink()
        if (
            not args.force
            and out_path.is_file()
            and out_path.stat().st_size > 0
        ):
            print(f"[ct_abnormality] cache hit: {volume_name}", file=sys.stderr)
            n_skipped += 1
            continue
        repo_path = _hf_path_for(volume_name, split_root)
        print(
            f"[ct_abnormality] downloading {repo_path}  →  {out_path}",
            file=sys.stderr,
        )
        # hf_hub_download with local_dir=... copies the file into our chosen
        # location AND keeps the HF cache intact for re-runs. We then move it
        # to the flat layout the entrypoint expects.
        staged = Path(
            hf_hub_download(
                repo_id=repo_id,
                filename=repo_path,
                repo_type="dataset",
                token=token,
                local_dir=str(args.cache_dir / ".hf_staging"),
            )
        )
        if out_path.exists() or out_path.is_symlink():
            # Existing file may be chmod 0444 from a prior freeze; force-remove
            # before rewriting.
            try:
                out_path.unlink()
            except PermissionError:
                # Strip write-bit on parent dir is not the issue; the file
                # itself is read-only. Use the standard fix.
                out_path.chmod(0o644)
                out_path.unlink()
        out_path.write_bytes(staged.read_bytes())
        if out_path.stat().st_size == 0:
            print(
                f"[ct_abnormality] downloaded file is empty: {out_path}",
                file=sys.stderr,
            )
            return 1
        # Freeze the volume read-only — matches the per-task entrypoint freeze
        # so the host cache layout is identical whether populated here or by a
        # cold-start container.
        out_path.chmod(0o444)
        n_downloaded += 1

    print(
        f"[ct_abnormality] OK: {n_total} volumes "
        f"({n_skipped} cache hits, {n_downloaded} downloaded) → {args.cache_dir}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
