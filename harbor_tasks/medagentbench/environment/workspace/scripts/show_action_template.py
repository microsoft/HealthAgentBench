#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: show_action_template.py <task_id>")
    task_id = sys.argv[1]
    templates_path = Path("/workspace/action_payload_templates.json")
    payload = json.loads(templates_path.read_text(encoding="utf-8"))
    if task_id not in payload:
        raise SystemExit(f"no action template for {task_id}")
    print(json.dumps(payload[task_id], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
