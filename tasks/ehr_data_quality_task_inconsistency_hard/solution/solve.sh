#!/bin/bash
set -euo pipefail
# Every task uses the same full audit, without hidden family selection.
python "$(dirname "$0")/oracle.py" \
    --data-dir /workspace/data/csv \
    --output /workspace/submission/flagged_rows.csv
