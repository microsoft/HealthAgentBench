#!/bin/bash
# MIMIC-CXR Report Correction Setup Script
#
# Downloads the dataset-wide assets the generator needs before producing
# the curated 10-case task tree. The generator only consults the three
# small CSVs below; per-patient prior reports + the target gold report
# are fetched JUST-IN-TIME by each trial's bootstrap container.
#
# Strictly required for ``--curated`` task generation (~30 MB total):
#   1. mimic-cxr-2.0.0-metadata.csv.gz  (~16 MB) — study dates + DICOM IDs
#   2. mimic-cxr-2.0.0-split.csv.gz     (~12 MB) — train/val/test split
#   3. mimic-cxr-2.0.0-chexpert.csv.gz  (~2 MB)  — disease labels
#
# Also downloaded for convenience (~3.5 GB; not used by ``--curated``):
#   - mimic-cxr-reports.zip — only needed by the legacy full-corpus
#     generation path; the correction task's bootstrap fetches
#     per-patient reports on demand. Skip with SKIP_REPORTS_ZIP=1.
#
# Per-patient JPGs are NEVER fetched here — each task container's
# bootstrap performs the same flock-guarded download on first run.
#
# Required env vars:
#   PN_USER   PhysioNet username
#   PN_PASS   PhysioNet password
#
# Optional env vars:
#   MIMIC_CXR_DATA_ROOT  (default: <repo>/scripts/xray_report_correction/assets)
#
# Usage:
#   PN_USER=... PN_PASS=... bash scripts/xray_report_correction/setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_ROOT="${MIMIC_CXR_DATA_ROOT:-$REPO_ROOT/scripts/xray_report_correction/assets}"
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

if [ "${SKIP_REPORTS_ZIP:-0}" = "1" ]; then
  echo "Step 1: SKIPPED — SKIP_REPORTS_ZIP=1 (per-patient reports fetched at"
  echo "         bootstrap; reports.zip is only needed by the legacy full-corpus path)."
else
  echo "Step 1: Downloading reports archive (~3.5 GB; set SKIP_REPORTS_ZIP=1 to skip)..."
  download_if_missing "$PN_BASE_REPORTS" "$REPORTS_DIR" "mimic-cxr-reports.zip"
fi

echo ""
echo "Step 2: Downloading split CSV..."
download_if_missing "$PN_BASE_JPG" "$JPG_DIR" "mimic-cxr-2.0.0-split.csv.gz"

echo ""
echo "Step 3: Downloading CheXpert label CSV (needed for disease-stratified sampling)..."
download_if_missing "$PN_BASE_JPG" "$JPG_DIR" "mimic-cxr-2.0.0-chexpert.csv.gz"

echo ""
echo "Step 4: Downloading metadata CSV (study dates + DICOM ids, needed for"
echo "         the --curated sampling so the generator can enumerate ALL"
echo "         priors per patient)..."
download_if_missing "$PN_BASE_JPG" "$JPG_DIR" "mimic-cxr-2.0.0-metadata.csv.gz"

echo ""
echo "===== Setup Complete ====="
echo ""
echo "Next: run the task generator. Per-patient JPGs are downloaded as the"
echo "generator writes each task manifest."
echo ""
echo "  uv run python scripts/xray_report_correction/generate_harbor_tasks.py \\"
echo "    --output-root tasks/xray_report_correction"
