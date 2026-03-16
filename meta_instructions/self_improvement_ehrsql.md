This guideline helps you organize your plan to improve an agent's capabilities to solve ehrsql task. 

STEP 1: Set up uv environment
Ensure Python ≥ 3.12 is installed, then run:
```bash
cd /home/qianchuliu/projects/MedCLI
uv sync --all-extras
source .venv/bin/activate
```

STEP 2: In the MedCLI repo directory and make sure your are in the branch flora/dev/harbor, run the current evaluation pipeline:
python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql \
  --sample-size 32 &&
source .venv/bin/activate && export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)" && timeout 1200 harbor run -c jobs/ehrsql_meta.yaml

STEP 3: Check the evaluation results in./result/harbor/{latest_time_stamp}/ Here is a quick navigation cheat sheet:

What you want to know,	File to check
Overall score,	result.json (top-level, look for "mean": ..)
How many passed,	verifier/meta_results.json
What SQL agent generated,	verifier/submission.json
Which tasks failed,	verifier/meta_results.json (error_taxonomy)
Why a specific task failed,	Compare in verifier/submission.json vs original task definition
Agent's reasoning,	agent/trajectory.json (long but detailed)
Errors/debug info	agent/logs_1.sqlite (SQLite database of logs)


STEP 4: After STEP 3, Append the results in /home/qianchuliu/projects/medcli_auto_improvement_results/ehrsql/results.csv, the run_id will be the branch name 'flora/dev/harbor' This will be the starting score for you to improve from

STEP 5: After STEP 4, create a new branch named flora/dev/harbor_ehrsql_improvement1, based on what you discovered in STEP 3, improve the agent workflow by **modifying the generator script** `scripts/ehrsql/generate_harbor_tasks.py`. You are allowed ONLY with the following changes:

**Important**: Do NOT manually edit files in `harbor_tasks/ehrsql/`. Instead, modify the generator functions to change what gets generated:
- **To add/modify helper scripts** → Edit the `_generate_primitive_scripts()` function in the generator
- **To improve instructions** → Edit the `_generate_instruction_md()` function in the generator

After modifying the generator, regenerate the artifacts:
```bash
uv run python scripts/ehrsql/generate_harbor_tasks.py \
  --output-root harbor_tasks/ehrsql \
  --sample-size 32
```

Make sure your improvements are robust and generalized, as they need to validate on different test sets in the future. 

STEP 6: Run STEP 2 - STEP 3 to run evaluation and analysis. 

STEP 7: Once you have achieved good improvement, you can append your results in /home/qianchuliu/projects/medcli_auto_improvement_results/ehrsql/results.csv The run_id will be your current branch name which is flora/dev/harbor_ehrsql_improvement1
