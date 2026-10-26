#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
if python -m pytest /tests/test_flagged_rows.py -rA; then
    echo "1.000000" > /logs/verifier/reward.txt
else
    echo "0.000000" > /logs/verifier/reward.txt
fi
