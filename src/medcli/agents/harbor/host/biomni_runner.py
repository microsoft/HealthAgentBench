"""Standalone Biomni runner launched through the host Biomni Python executable."""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any


def sanitize_sys_path_for_biomni(script_path: Path, sys_path: list[str]) -> list[str]:
    """Remove local MedCLI script directories that can shadow the real Biomni package."""

    script_dir = str(script_path.resolve().parent)
    return [
        entry
        for entry in sys_path
        if Path(entry or ".").resolve().as_posix() != script_dir
    ]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("runner config must be a JSON object")
    return payload


def _write_result(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = _parse_args()
    config = _load_json(args.config)
    result_path = Path(str(config["result_path"])).expanduser().resolve()
    result_path.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    try:
        sys.path[:] = sanitize_sys_path_for_biomni(Path(__file__), sys.path)
        from biomni.agent import A1

        llm = config.get("llm")
        data_path = str(config["data_path"])
        mcp_config_path = str(config["mcp_config_path"])
        instruction = str(config["instruction"])

        if llm:
            agent = A1(path=data_path, llm=llm)
        else:
            agent = A1(path=data_path)

        if mcp_config_path:
            agent.add_mcp(config_path=mcp_config_path)

        log, final_response = agent.go(instruction)
        elapsed = time.monotonic() - started
        _write_result(
            result_path,
            {
                "status": "ok",
                "elapsed_seconds": elapsed,
                "final_response": final_response,
                "log_entries": len(log) if isinstance(log, list) else None,
            },
        )
    except Exception as exc:
        elapsed = time.monotonic() - started
        _write_result(
            result_path,
            {
                "status": "error",
                "elapsed_seconds": elapsed,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        raise


if __name__ == "__main__":
    main()
