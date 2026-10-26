#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
exec python verify_meta_task.py
