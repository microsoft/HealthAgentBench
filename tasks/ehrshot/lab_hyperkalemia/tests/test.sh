#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p /logs/verifier /logs/artifacts
python verify.py
