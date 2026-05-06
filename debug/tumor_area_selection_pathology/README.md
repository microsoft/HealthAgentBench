# Tumor Area Selection Pathology Debug

Use the generic Harbor debug workflow in `debug/README.md` with these
benchmark-specific settings:

- `HB_TASK_DIR=tasks/tumor_area_selection_pathology/<task_name>`
- `HB_PROJECT_NAME=tumor-area-selection-debug`

The task entrypoint materializes the current slide under
`/data/slide/current/slide.*` and writes a public manifest to
`/data/slide/current/manifest.json`. The agent-visible workspace contains:

- `/workspace/benchmark_tasks.json`
- `/workspace/submission.json`
- `/workspace/scripts/primitives/*.py`

## Manual Replay

After the generator has produced a specific slide task, a human can replay the
task manually in a fresh container:

```bash
cd tasks/tumor_area_selection_pathology/<task_name>/environment
docker compose up --detach --wait main
docker compose exec main bash

# --- inside the container ---

ls /workspace
cat /workspace/benchmark_tasks.json | jq .
cat /data/slide/current/manifest.json | jq .

python /workspace/scripts/primitives/get_slide_thumbnail.py --max-size 1024
python /workspace/scripts/primitives/sample_tiles.py --count 20
python /workspace/scripts/primitives/get_tile.py --x 0 --y 0

python - <<'PY'
import json, pathlib
path = pathlib.Path('/workspace/submission.json')
data = json.loads(path.read_text())
data[0]['contains_tumor'] = False
data[0]['predicted_tumor_tiles'] = []
path.write_text(json.dumps(data, indent=2))
PY

bash /tests/test.sh
cat /logs/verifier/meta_results.json
cat /logs/verifier/reward.json
```

If the verifier runs and writes a reward payload, the task / environment /
verifier path is healthy. At that point, any Harbor failure should be treated
as likely agent behavior rather than a benchmark wiring problem.
