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
ls /workspace/scripts/primitives
python /workspace/scripts/primitives/get_patient.py --help
python /workspace/scripts/primitives/get_patient.py --identifier S2874099
python /workspace/scripts/primitives/get_observation_labs.py --patient S2823623 --code GLU
python /workspace/scripts/primitives/post_servicerequest.py --help
sed -n "1,120p" /workspace/submission.json
'
