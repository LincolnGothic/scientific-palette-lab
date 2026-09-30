#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -x .venv/bin/python ]]; then
  task_python=.venv/bin/python
elif python3 -c 'import numpy, PIL' 2>/dev/null; then
  task_python=python3
else
  task_python=""
  for candidate in "$HOME"/.cache/codex-runtimes/*/dependencies/python/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import numpy, PIL' 2>/dev/null; then
      task_python="$candidate"
      break
    fi
  done
  if [[ -z "$task_python" ]]; then
    echo "Create an environment first: python3 -m venv .venv && .venv/bin/pip install -e ." >&2
    exit 1
  fi
fi
if [[ $# -eq 0 ]]; then
  set -- serve
fi
exec "$task_python" -m palette_lab "$@"
