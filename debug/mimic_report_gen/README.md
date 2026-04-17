# MIMIC-CXR Report Generation Debug

Use the generic Harbor debug workflow in `debug/README.md` with these benchmark-specific settings:

- `HB_TASK_DIR=tasks/mimic_report_gen/<patient_study_id>` (one task dir per patient)
- `HB_PROJECT_NAME=mimic-report-gen-debug`
- `PN_USER` / `PN_PASS` must be exported so the container entrypoint can fetch any missing JPGs from PhysioNet via the flock-guarded bootstrap.

The task expects the agent to view images in `/data/patient/<timestamp>_<study>/<dicom_id>.jpg`, read prior reports at `/data/patient/<timestamp>_<study>/report.txt`, and write a `final_answer` containing `FINDINGS:` and `IMPRESSION:` sections to `/workspace/submission.json`. The target-study folder intentionally has no `report.txt`.

The verifier computes per-trial BLEU-4 and ROUGE-L against the held-out target report, runs CheXbert on both reference and prediction, and emits 28 scalar label fields (`chx_ref_<label>` / `chx_pred_<label>`) to `reward.json`. The pooled CheXbert F1-14 is computed across trials by the `uv-script` aggregator at `scripts/mimic_report_gen/aggregate_metric.py`.

## Manual Replay

After the generator has produced a specific patient task, a human can execute the same workflow manually inside a fresh task container to distinguish agent failures from task / environment / verifier failures:

```bash
# 1. Build and start the task container.
cd tasks/mimic_report_gen/<patient_study_id>/environment
docker compose up --detach --wait main
docker compose exec main bash

# --- inside the container ---

# 2. Inspect the agent-visible workspace.
ls /workspace                                # benchmark_tasks.json, submission.json, README.md
cat /workspace/benchmark_tasks.json | jq .

# 3. Inspect the materialized patient data.
ls /data/patient                             # manifest.json + timestamped folders
cat /data/patient/manifest.json | jq .
for f in /data/patient/*/report.txt; do
  echo "=== $f ==="
  cat "$f"
done

# 4. Inspect the target study's images (target folder has NO report.txt).
ls /data/patient/$(jq -r '.studies[] | select(.is_target) | .folder' \
                   /data/patient/manifest.json)

# 5. Write a hand-crafted FINDINGS + IMPRESSION into submission.json
#    via a JSON-aware tool.
python - <<'PY'
import json, pathlib
path = pathlib.Path("/workspace/submission.json")
data = json.loads(path.read_text())
data[0]["final_answer"] = """FINDINGS:
No acute cardiopulmonary process. Stable cardiomediastinal silhouette.

IMPRESSION:
No acute cardiopulmonary findings."""
path.write_text(json.dumps(data, indent=2))
PY

# 6. Run the verifier.
bash /tests/test.sh
cat /logs/verifier/meta_results.json
cat /logs/verifier/reward.json
```

If step 6 produces a non-empty `reward.json` with `chx_ref_*` and `chx_pred_*` scalar fields populated and no `chexbert_error.txt`, the task / environment / verifier are all healthy; any real-agent failure should then be investigated as an agent-execution or instruction-following bug.
