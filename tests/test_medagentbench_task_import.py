import subprocess
from pathlib import Path

import yaml

from ehr_co_scientist.tools.catalog import TOOL_REGISTRY


def test_import_groups_into_task_type_manifests(tmp_path: Path):
    output_root = tmp_path / "tasks"

    cmd = [
        ".venv/bin/python",
        "scripts/medagentbench/import_tasks.py",
        "--input",
        "data/medagentbench/test_data_v2.json",
        "--funcs-json",
        "data/medagentbench/funcs_v1.json",
        "--output-root",
        str(output_root),
        "--split",
        "std",
    ]
    subprocess.run(cmd, check=True)

    manifests = sorted(output_root.glob("*/sources/medagentbench/std.yaml"))
    assert manifests

    total = 0
    for manifest in manifests:
        payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        tasks = payload["tasks"]
        total += len(tasks)
        for task in tasks:
            allowed = task.get("allowed_tools", [])
            assert set(allowed).issubset(TOOL_REGISTRY.keys())

    assert total == 300
