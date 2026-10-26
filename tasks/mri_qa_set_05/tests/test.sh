#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
echo 0.0 > /logs/verifier/reward.txt
python /tests/verify.py
