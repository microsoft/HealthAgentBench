#!/bin/bash
# MIMIC-CXR Report Generation Setup Script
#
# Downloads the two dataset-wide assets required before task generation:
#   1. mimic-cxr-reports.zip            (all radiology reports)
#   2. mimic-cxr-2.0.0-split.csv.gz     (train/val/test split CSV)
#
# Per-patient JPGs are NOT fetched here — the generator downloads the
# specific image subset it needs when tasks are created. If assets are
# still missing at Harbor run time, each task container's entrypoint.sh
# performs the same download (flock-guarded).
#
# Required env vars:
#   PN_USER   PhysioNet username
#   PN_PASS   PhysioNet password
#
# Optional env vars:
#   MIMIC_CXR_DATA_ROOT  (default: <repo>/scripts/mimic_report_gen/assets)
#
# Usage:
#   PN_USER=... PN_PASS=... bash scripts/mimic_report_gen/setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_ROOT="${MIMIC_CXR_DATA_ROOT:-$REPO_ROOT/scripts/mimic_report_gen/assets}"
REPORTS_DIR="$DATA_ROOT/mimic-cxr/2.1.0"
JPG_DIR="$DATA_ROOT/mimic-cxr-jpg/2.1.0"
LOCK_DIR="$DATA_ROOT/.locks"

PN_BASE_REPORTS="https://physionet.org/files/mimic-cxr/2.1.0"
PN_BASE_JPG="https://physionet.org/files/mimic-cxr-jpg/2.1.0"

if [ -z "${PN_USER:-}" ] || [ -z "${PN_PASS:-}" ]; then
  echo "ERROR: set PN_USER and PN_PASS (PhysioNet credentials) before running" >&2
  exit 1
fi

mkdir -p "$REPORTS_DIR" "$JPG_DIR" "$LOCK_DIR"

# Serialize concurrent invocations (host-side setup and container-side
# bootstrap both flock on this file).
LOCK_FILE="$LOCK_DIR/mimic-cxr-setup.lock"
exec 9>"$LOCK_FILE"
echo "Acquiring setup lock at $LOCK_FILE..."
flock 9
echo "Lock acquired."

echo "===== MIMIC-CXR Report Generation Setup ====="
echo "Data root:   $DATA_ROOT"
echo "Reports dir: $REPORTS_DIR"
echo "JPG dir:     $JPG_DIR"
echo ""

download_if_missing() {
  local url=$1
  local target_dir=$2
  local target_name=$3
  local target="$target_dir/$target_name"
  if [ -s "$target" ]; then
    echo "  ✓ $target_name already present"
    return 0
  fi
  echo "  Downloading $target_name..."
  wget -c -q --show-progress -P "$target_dir" \
    --user "$PN_USER" --password "$PN_PASS" \
    "$url/$target_name"
  echo "  ✓ Downloaded $target_name"
}

echo "Step 1: Downloading reports archive..."
download_if_missing "$PN_BASE_REPORTS" "$REPORTS_DIR" "mimic-cxr-reports.zip"

echo ""
echo "Step 2: Downloading split CSV..."
download_if_missing "$PN_BASE_JPG" "$JPG_DIR" "mimic-cxr-2.0.0-split.csv.gz"

echo ""
echo "===== Setup Complete ====="
echo ""
echo "Next: run the task generator. Per-patient JPGs are downloaded as the"
echo "generator writes each task manifest."
echo ""
echo "  uv run python scripts/mimic_report_gen/generate_harbor_tasks.py \\"
echo "    --output-root tasks/mimic_report_gen"
