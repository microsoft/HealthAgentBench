This guideline helps you organize your plan to improve an agent's capabilities to solve ehrsql task. 


STEP 1: In the MedCLI repo directory and make sure your are in the branch flora/dev/harbor, 

STEP 2: In the MedCLI repo directory, run the current evaluation pipeline:
source .venv/bin/activate && export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)" && timeout 600 harbor run -c jobs/ehrsql_meta.yaml

STEP 3: Check the evaluation results in./result/harbor/{latest_time_stamp}/ Here is a quick navigation cheat sheet:

What you want to know,	File to check
Overall score,	result.json (top-level, look for "mean": 0.625)
How many passed,	verifier/meta_results.json
What SQL agent generated,	verifier/submission.json
Which tasks failed,	verifier/meta_results.json (error_taxonomy)
Why a specific task failed,	Compare in verifier/submission.json vs original task definition
Agent's reasoning,	agent/trajectory.json (long but detailed)
Errors/debug info	agent/logs_1.sqlite (SQLite database of logs)


STEP 4: Now append the results in /home/qianchuliu/projects/medcli_auto_improvement_results/ehrsql/results.csv, the run_id will be the branch name 'flora/dev/harbor' This will be the starting score for you to improve from

STEP 5: Now create a new branch named flora/dev/harbor/ehrsql_improvement0, based on what you discovered in STEP 3, you can improve the agent workflow by changing only the following:
    1. You can add or modify any helper functions or add tools in harbor_tasks/ehrsql/workspaced/scripts
    2. You can improve on harbor_tasks/ehrsql/instruction.md
Make sure your changes should be improving the agent workflow in a robust and generalized way as we need to validate on a different test set in the future. 

STEP 6: Run STEP 2 - STEP 3 to run evaluation and analysis. 

STEP 7: Once you have achieved good improvement, you can append your results in /home/qianchuliu/projects/medcli_auto_improvement_results/ehrsql/results.csv The run_id will be your current branch name which is flora/dev/harbor/ehrsql_improvement0
