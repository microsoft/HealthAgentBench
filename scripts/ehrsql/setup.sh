#!/bin/bash

# EHRSQL Setup Script
# Downloads and validates EHRSQL dataset assets for Harbor-based workflow
# Usage: bash scripts/ehrsql/setup.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="${REPO_ROOT}/scripts/ehrsql/assets"
GITHUB_BASE="https://raw.githubusercontent.com/glee4810/EHRSQL/main/dataset/ehrsql"

echo "===== EHRSQL Harbor Setup ====="
echo "Data directory: $DATA_DIR"
mkdir -p "$DATA_DIR/mimic_iii" "$DATA_DIR/eicu"

# ===== Download JSON Files =====
echo ""
echo "Step 1: Downloading task JSON files..."

FILES=(
  "mimic_iii/valid.json"
  "mimic_iii/test.json"
  "eicu/valid.json"
  "eicu/test.json"
  "tables.json"
)

for file in "${FILES[@]}"; do
  target_path="$DATA_DIR/$file"
  if [ -f "$target_path" ]; then
    echo "  ✓ $file already exists"
  else
    echo "  Downloading $file..."
    curl -sSf "${GITHUB_BASE}/${file}" -o "$target_path"
    if [ $? -eq 0 ]; then
      echo "  ✓ Downloaded $file"
    else
      echo "  ✗ Failed to download $file"
      exit 1
    fi
  fi
done

# ===== Validate Schemas =====
echo ""
echo "Step 2: Validating schemas..."

validate_task_json() {
  local file=$1
  echo "  Validating $file..."

  # Check if file is valid JSON
  if ! python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
    echo "  ✗ Invalid JSON in $file"
    return 1
  fi

  # Check required fields (basic validation)
  python3 << EOF
import json
data = json.load(open('$file'))
if not isinstance(data, list):
  print(f"  ✗ Expected list of tasks, got {type(data).__name__}")
  exit(1)

required_fields = {'question', 'db_id', 'is_impossible', 'query'}
for i, task in enumerate(data[:5]):  # Check first 5
  missing = required_fields - set(task.keys())
  if missing:
    print(f"  ✗ Task {i} missing fields: {missing}")
    exit(1)

print(f"  ✓ Schema valid ({len(data)} tasks)")
EOF

  return $?
}

for file in "valid.json" "test.json"; do
  validate_task_json "$DATA_DIR/mimic_iii/$file" || exit 1
  validate_task_json "$DATA_DIR/eicu/$file" || exit 1
done

# Validate tables.json
echo "  Validating tables.json..."
python3 << EOF
import json
tables = json.load(open('$DATA_DIR/tables.json'))
if not isinstance(tables, list):
  print(f"  ✗ Expected list of databases, got {type(tables).__name__}")
  exit(1)

db_ids = {t['db_id'] for t in tables}
if 'mimic_iii' not in db_ids or 'eicu' not in db_ids:
  print(f"  ✗ Missing MIMIC-III or eICU in tables")
  exit(1)

print(f"  ✓ Tables schema valid ({len(tables)} databases)")
EOF
[ $? -eq 0 ] || exit 1

# ===== Generate SHA256SUMS =====
echo ""
echo "Step 3: Generating SHA256SUMS..."
cd "$DATA_DIR"
{
  sha256sum mimic_iii/valid.json
  sha256sum mimic_iii/test.json
  sha256sum eicu/valid.json
  sha256sum eicu/test.json
  sha256sum tables.json
} > SHA256SUMS
echo "  ✓ SHA256SUMS generated"

# ===== SQLite Database Download =====
echo ""
echo "Step 4: SQLite database setup (required for Harbor environment)..."
echo ""

# Function to download from Google Drive
download_from_google_drive() {
  local file_id=$1
  local output_path=$2
  local file_name=$(basename "$output_path")

  echo "  Downloading $file_name..."

  # Try using gdown if available
  if command -v gdown &> /dev/null; then
    gdown "https://drive.google.com/uc?id=$file_id" -O "$output_path" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo "  ✓ Downloaded $file_name"
      return 0
    fi
  fi

  # Fallback: use curl with Google Drive URL
  # Note: This requires confirming the download on first attempt
  echo "  Attempting download with curl (you may need to confirm in browser)..."
  curl -L "https://drive.google.com/uc?id=$file_id&export=download" \
    -o "$output_path" \
    -b /tmp/cookies.txt -c /tmp/cookies.txt 2>/dev/null

  if [ -f "$output_path" ] && [ -s "$output_path" ]; then
    echo "  ✓ Downloaded $file_name"
    return 0
  fi

  return 1
}

MIMIC_FILE_ID="17FkHhaQrmSz5-W2b7WEy90duKfvjBn5x"
EICU_FILE_ID="1JG9DUdeJeuIXShK6DdEJ61NEyPiaGEKZ"

MIMIC_PATH="$DATA_DIR/mimic_iii/mimic_iii.sqlite"
EICU_PATH="$DATA_DIR/eicu/eicu.sqlite"

# Check if databases already exist
if [ -f "$MIMIC_PATH" ] && [ -f "$EICU_PATH" ]; then
  echo "✓ Both SQLite databases found!"
else
  echo ""
  echo "IMPORTANT: EHRSQL Harbor requires SQLite databases (95 MB + 102 MB)."
  echo ""
  echo "Attempting to download from Google Drive..."
  echo ""

  download_success=true

  # Download MIMIC-III if not present
  if [ ! -f "$MIMIC_PATH" ]; then
    if ! download_from_google_drive "$MIMIC_FILE_ID" "$MIMIC_PATH"; then
      download_success=false
      echo "  ⚠ Failed to download MIMIC-III. See manual download below."
    fi
  else
    echo "  ✓ MIMIC-III database already present"
  fi

  # Download eICU if not present
  if [ ! -f "$EICU_PATH" ]; then
    if ! download_from_google_drive "$EICU_FILE_ID" "$EICU_PATH"; then
      download_success=false
      echo "  ⚠ Failed to download eICU. See manual download below."
    fi
  else
    echo "  ✓ eICU database already present"
  fi

  if [ "$download_success" = false ]; then
    echo ""
    echo "Manual Download Instructions:"
    echo "================================"
    echo ""
    echo "1. Download MIMIC-III (95 MB):"
    echo "   https://drive.google.com/file/d/17FkHhaQrmSz5-W2b7WEy90duKfvjBn5x/view?usp=sharing"
    echo "   → Save to: $MIMIC_PATH"
    echo ""
    echo "2. Download eICU (102 MB):"
    echo "   https://drive.google.com/file/d/1JG9DUdeJeuIXShK6DdEJ61NEyPiaGEKZ/view?usp=sharing"
    echo "   → Save to: $EICU_PATH"
    echo ""
    echo "Alternatively, install gdown for easier automated downloads:"
    echo "   pip install gdown"
    echo "   bash scripts/ehrsql/setup.sh  # Run setup again"
  fi
fi

# Verify databases exist and are valid SQLite files
echo ""
echo "Step 5: Validating SQLite databases..."

verify_sqlite_db() {
  local db_path=$1
  local db_name=$(basename "$db_path")

  if [ ! -f "$db_path" ]; then
    echo "  ✗ $db_name not found"
    return 1
  fi

  local file_size=$(stat -f%z "$db_path" 2>/dev/null || stat -c%s "$db_path" 2>/dev/null)
  if [ "$file_size" -lt 1000000 ]; then  # Less than 1MB is too small
    echo "  ✗ $db_name is corrupted (size: ${file_size} bytes, should be >90MB)"
    return 1
  fi

  if ! sqlite3 "$db_path" ".tables" &>/dev/null; then
    echo "  ✗ $db_name is not a valid SQLite database"
    return 1
  fi

  echo "  ✓ $db_name is valid ($(numfmt --to=iec-i --suffix=B $file_size 2>/dev/null || echo "$file_size bytes"))"
  return 0
}

mimic_valid=false
eicu_valid=false

verify_sqlite_db "$MIMIC_PATH" && mimic_valid=true
verify_sqlite_db "$EICU_PATH" && eicu_valid=true

if [ "$mimic_valid" = true ] && [ "$eicu_valid" = true ]; then
  echo ""
  echo "✓ All required SQLite databases are valid and in place!"
else
  echo ""
  echo "⚠ One or more SQLite databases are invalid or missing:"
  if [ "$mimic_valid" = false ]; then
    echo "  - MIMIC-III: corrupted or missing"
    rm -f "$MIMIC_PATH"
  fi
  if [ "$eicu_valid" = false ]; then
    echo "  - eICU: corrupted or missing"
    rm -f "$EICU_PATH"
  fi
  echo ""
  echo "Please download manually using the links above."
  echo "Run setup.sh again after placing the files in the correct location."
fi

echo ""
echo "===== Setup Complete ====="
echo ""
echo "Next steps:"
echo "  1. If databases weren't downloaded, download them manually from the links above"
echo "  2. Run the Harbor generator:"
echo "     uv run python scripts/ehrsql/generate_harbor_tasks.py --output-root harbor_tasks/ehrsql"
echo ""
echo "Tip: Install gdown for automated downloads in future runs:"
echo "  pip install gdown"
