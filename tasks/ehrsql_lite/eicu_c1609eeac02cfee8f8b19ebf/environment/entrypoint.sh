#!/bin/bash
set -e

DB_PATH="/data/ehrsql/eicu/eicu.sqlite"
LOCK_FILE="${DB_PATH}.lock"

if [ ! -f "$DB_PATH" ]; then
  mkdir -p "$(dirname "$DB_PATH")"
  # Use flock so only one worker downloads; others wait then see the file
  (
    flock 9
    if [ ! -f "$DB_PATH" ]; then
      echo "Database not found at $DB_PATH. Downloading..."
      gdown "https://drive.google.com/uc?id=1JG9DUdeJeuIXShK6DdEJ61NEyPiaGEKZ" -O "${DB_PATH}.tmp"
      mv "${DB_PATH}.tmp" "$DB_PATH"
      echo "Download complete."
    fi
  ) 9>"$LOCK_FILE"
fi

# Protect database from accidental writes during agent execution
chmod 444 "$DB_PATH"

exec "$@"
