#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p /logs/verifier /logs/artifacts
# Fail closed: a missing or malformed submission scores 0 instead of raising.
echo 0.0 > /logs/verifier/reward.txt
python verify.py
