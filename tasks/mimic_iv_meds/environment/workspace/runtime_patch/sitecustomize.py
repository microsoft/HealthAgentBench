from __future__ import annotations

import importlib
from pathlib import Path

PATTERN = "        lock.release()\n        lock_fp.unlink()\n"
REPLACEMENT = "        lock.release()\n        if lock_fp.exists():\n            lock_fp.unlink()\n"


def _apply_meds_lock_patch() -> None:
    try:
        import MEDS_transforms.mapreduce.utils as utils
    except Exception:
        return

    target = Path(utils.__file__)
    text = target.read_text(encoding="utf-8")
    if REPLACEMENT in text:
        return
    if PATTERN not in text:
        return

    target.write_text(text.replace(PATTERN, REPLACEMENT), encoding="utf-8")
    importlib.reload(utils)


_apply_meds_lock_patch()
