#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /logs/artifacts

: "${VERIFIER_ERROR_ANALYSIS_FILE:=/logs/artifacts/error_analysis.json}"

python /tests/verify_output.py   --repo-dir /workspace/MIMIC_IV_MEDS   --output-root /workspace/output   --gold-summary /tests/gold_demo_summary.json   --reward-file /logs/verifier/reward.txt   --error-analysis-file "${VERIFIER_ERROR_ANALYSIS_FILE}"
