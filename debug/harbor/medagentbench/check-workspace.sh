#!/usr/bin/env bash
# Run basic MedAgentBench workspace checks inside the live Harbor task
# container. This is a task-specific sanity pass, not a verifier.
set -euo pipefail
source "$(dirname "$0")/../common.sh"

hb::setup_task_env
hb::compose exec "${HB_MAIN_SERVICE}" bash -lc '
set -euo pipefail
ls /workspace
ls /workspace/scripts
/workspace/scripts/wait_for_fhir.sh
python /workspace/scripts/fhir_tools.py patient-age --mrn S2874099
python /workspace/scripts/fhir_tools.py latest-observation --patient S2823623 --code GLU
python /workspace/scripts/show_action_template.py task8_1
python /workspace/scripts/init_submission.py
sed -n "1,120p" /workspace/submission.json
'
