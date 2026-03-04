import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
def test_medagentbench_smoke(tmp_path: Path):
    if os.environ.get("RUN_MEDAGENTBENCH_SMOKE") != "1":
        pytest.skip("Set RUN_MEDAGENTBENCH_SMOKE=1 to run integration smoke test.")

    subprocess.run(["bash", "scripts/medagentbench/fhir_up.sh"], check=True)
    try:
        run_cmd = [
            ".venv/bin/python",
            "experiments/run.py",
            "--task",
            "medagentbench",
            "--split",
            "std",
            "--max-tasks",
            "3",
            "--backend",
            "mock",
            "--model",
            "gpt-5.2",
            "--fhir-base-url",
            "http://localhost:8080/fhir",
            "--output-dir",
            str(tmp_path / "run"),
        ]
        subprocess.run(run_cmd, check=True)

        results_path = tmp_path / "run" / "results.jsonl"
        assert results_path.exists()

        eval_cmd = [
            ".venv/bin/python",
            "benchmarks/evaluate.py",
            "--task",
            "medagentbench",
            "--results",
            str(results_path),
        ]
        subprocess.run(eval_cmd, check=True)

        summary_json = tmp_path / "run" / "summary.json"
        assert summary_json.exists()
        payload = json.loads(summary_json.read_text(encoding="utf-8"))
        assert payload["total_tasks"] == 3
    finally:
        subprocess.run(["bash", "scripts/medagentbench/fhir_down.sh"], check=False)
