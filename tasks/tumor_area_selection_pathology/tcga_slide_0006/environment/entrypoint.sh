#!/bin/bash
set -euo pipefail

MANIFEST=/opt/task_manifest.json
DEST=/data/slide/current

python3 - <<'PY'
import json
import os
import shutil
import urllib.request
from pathlib import Path

manifest = json.loads(Path("/opt/task_manifest.json").read_text(encoding="utf-8"))
dest = Path("/data/slide/current")
dest.mkdir(parents=True, exist_ok=True)

subset = manifest["subset"]
extension = manifest["slide_extension"]
download_url = manifest["download_url"]

if subset == "tcga":
    cache_root = Path("/data/cache/tcga")
    cache_name = f"{manifest['source_file_id']}{extension}"
else:
    cache_root = Path("/data/cache/camelyon16/slides")
    cache_name = f"{manifest['source_slide_name']}{extension}"

cache_root.mkdir(parents=True, exist_ok=True)
cached_path = cache_root / cache_name
lock_path = cache_root / f"{cache_name}.lock"

with lock_path.open("w") as lock_file:
    import fcntl
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
    if not cached_path.exists() or cached_path.stat().st_size == 0:
        tmp_path = cached_path.with_suffix(cached_path.suffix + ".part")
        with urllib.request.urlopen(download_url, timeout=600) as response, tmp_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        tmp_path.replace(cached_path)

public_manifest = {
    "task_id": manifest["task_id"],
    "subset": manifest["subset"],
    "tile_size": manifest["tile_size"],
    "analysis_downsample": manifest["analysis_downsample"],
    "slide_path": f"/data/slide/current/slide{extension}",
}
slide_dest = dest / f"slide{extension}"
if slide_dest.exists() or slide_dest.is_symlink():
    slide_dest.unlink()
os.symlink(cached_path, slide_dest)
(dest / "manifest.json").write_text(json.dumps(public_manifest, indent=2) + "\n", encoding="utf-8")
PY

exec "$@"
