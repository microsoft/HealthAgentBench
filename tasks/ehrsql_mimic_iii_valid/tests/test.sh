#!/bin/bash
# Harbor test script for EHRSQL verification

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

# Run the verifier
python verify_meta_task.py
