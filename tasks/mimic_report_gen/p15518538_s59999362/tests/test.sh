#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
python verify_meta_task.py
