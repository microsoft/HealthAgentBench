from __future__ import annotations

import argparse
from pathlib import Path

PATTERN = "        lock.release()\n        lock_fp.unlink()\n"
REPLACEMENT = "        lock.release()\n        if lock_fp.exists():\n            lock_fp.unlink()\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("venv_dir", type=Path)
    args = parser.parse_args()

    target = args.venv_dir / "lib" / "python3.11" / "site-packages" / "MEDS_transforms" / "mapreduce" / "utils.py"
    text = target.read_text(encoding="utf-8")
    if PATTERN not in text:
        raise SystemExit(f"Expected patch target not found in {target}")
    target.write_text(text.replace(PATTERN, REPLACEMENT), encoding="utf-8")
    print(f"Patched {target}")


if __name__ == "__main__":
    main()
