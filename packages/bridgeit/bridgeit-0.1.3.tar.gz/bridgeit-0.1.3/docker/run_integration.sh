#!/usr/bin/env bash
set -euo pipefail

cd /workspace
if [[ -n "${EXTRA_PATH:-}" ]]; then
  export PATH="${EXTRA_PATH}:${PATH}"
fi
export PATH="${HOME}/.local/bin:${PATH}"
pip install --no-cache-dir -e .
python docker/execute_notebooks.py "$@"
