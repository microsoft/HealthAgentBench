# MIMIC-CXR Report Correction Debug

Use the generic Harbor debug workflow in `debug/README.md` with these
benchmark-specific settings:

- `HB_TASK_DIR=tasks/xray_report_correction/case_<NN>` (one task dir per
  curated patient, `case_01` through `case_10`)
- `HB_PROJECT_NAME=xray-correction-debug`
- `PN_USER` / `PN_PASS` must be exported so the `bootstrap` compose
  service can fetch any missing JPGs + the target gold report from
  PhysioNet.

The agent reads the per-patient prior reports + images under
`/data/patient/study_*/`, finds the **target** study (highest-numbered
`study_NN_<timestamp>/` folder), reviews its **draft FINDINGS** (already
populated by bootstrap with deliberate clinical errors), and writes a
corrected `FINDINGS:` body into `/workspace/submission.json` under
`final_answer`. No `IMPRESSION:` section is expected — the verifier
scores `FINDINGS:` only.

The verifier (`scripts/xray_report_correction/harbor_evaluator.py`)
runs **CheXprompt** five times against the gold FINDINGS (5-of-5
majority; pass iff ≥3 votes return zero clinically-significant errors)
and emits `reward.json` with `reward`, `pass_rate`, and `mean_sig_errors`.

## Manual Replay

After the generator has produced the case directories, a human can
execute the entire workflow manually inside a fresh task container to
distinguish **agent failures** from **task / environment / verifier
failures**. The point is to reach a clean `reward.json` without invoking
an agent.

```bash
# 1. Build + start the task container (case_04 is a good probe — its
#    8 phrase swaps cover P1, P2, P3, P6, and P7 categories).
cd tasks/xray_report_correction/case_04/environment
docker compose --project-name xray_correction_manual up --detach --wait main
docker compose --project-name xray_correction_manual exec main bash

# --- inside the container ---

# 2. Confirm the bootstrap landed the corrupted draft in the target
#    study's report.txt.
target=$(ls -d /data/patient/study_*/ | sort | tail -1)
echo "target study: $target"
sed -n '/^FINDINGS:/,/^$/p' "$target/report.txt"

# 3. Confirm the per-study JPGs are readable (real files, not broken
#    symlinks). Should print 1-3 lines, each >1 MB.
for f in /data/patient/study_*/view_*.jpg; do
  [ -r "$f" ] && echo "READABLE: $f $(stat -L -c %s "$f")B" || echo "BROKEN:   $f"
done

# 4. Write a corrected FINDINGS into /workspace/submission.json using a
#    JSON-aware tool. For case_04 the gold FINDINGS is:
python3 - <<'PY'
import json, pathlib
sub = pathlib.Path("/workspace/submission.json")
data = json.loads(sub.read_text())
data[0]["final_answer"] = (
    "FINDINGS:\n"
    "Endotracheal tube ends approximately 4.8 cm above the carina and is "
    "appropriate in position. Intraaortic balloon pump lies approximately "
    "2.6 cm from the apex of the aortic arch. The patient is status post "
    "median sternotomy with intact sternal sutures. Gastric tube courses "
    "below the diaphragm into the stomach; however, its distal end is "
    "beyond the field of view. Asymmetric, mild, right pulmonary edema "
    "has improved over last 24 hours. Normal heart size. The mediastinal "
    "and hilar contours are unchanged. There is no pleural effusion."
)
sub.write_text(json.dumps(data, indent=2))
PY

# 5. Run the verifier. Requires AZURE_OPENAI_* (or OPENAI_API_*) and
#    CHEXPROMPT_DEPLOYMENT in the container env — they're pulled in from
#    .env by the compose env_file.
bash /tests/test.sh

# 6. Inspect the outputs.
cat /logs/verifier/reward.json    # → {"reward": 1.0, "n_tasks": 1,
                                  #     "n_pass": 1, "pass_rate": 1.0,
                                  #     "mean_sig_errors": 0.0}
jq .results /logs/verifier/metrics.json
```

A clean replay produces `reward = 1.0` and `mean_sig_errors = 0.0`. If
the run instead yields a non-zero `mean_sig_errors`, the gold report
fetched at bootstrap diverges from the swap-rules' source phrases —
inspect `/tests/target_report.txt` and re-run
`pytest tests/test_xray_report_correction_swap_rules.py` against the
host repo to surface the rotted rule.

### Verifier-fails-closed replay

To confirm the verifier rejects bad output as expected, write an empty
or obviously-wrong FINDINGS and re-run step 5:

```bash
python3 - <<'PY'
import json, pathlib
sub = pathlib.Path("/workspace/submission.json")
data = json.loads(sub.read_text())
data[0]["final_answer"] = ""        # empty → no candidate findings
sub.write_text(json.dumps(data, indent=2))
PY

bash /tests/test.sh
cat /logs/verifier/reward.json
# → {"reward": 0.0, "n_tasks": 1, "n_pass": 0, "pass_rate": 0.0}
# Note: ``mean_sig_errors`` is deliberately omitted on empty
# submissions so the diagnostic mean isn't biased toward 0.
```

If both replays behave as above, the task / environment / verifier are
healthy; any Harbor run failure should then be investigated as an
agent-execution or instruction-following bug.

### Cleanup

```bash
exit                                                       # leave the container shell
docker compose --project-name xray_correction_manual down -v
```
