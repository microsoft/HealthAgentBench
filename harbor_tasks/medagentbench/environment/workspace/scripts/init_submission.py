#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    template = Path("/workspace/submission_template.json")
    target = Path("/workspace/submission.json")
    if target.exists():
        print(f"already exists: {target}")
        return
    shutil.copyfile(template, target)
    print(f"created {target}")


if __name__ == "__main__":
    main()
