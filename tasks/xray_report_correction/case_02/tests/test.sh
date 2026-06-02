#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
exec /opt/verifier-venv/bin/python verify_meta_task.py
