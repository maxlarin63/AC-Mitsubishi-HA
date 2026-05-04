#!/usr/bin/env bash
# Ensure a working .venv (Python 3.12) at the repo root.
# - No-op if .venv/bin/python already exists.
# - Otherwise: create the venv with `python3.12 -m venv` and install requirements-dev.txt.
# Used as a `dependsOn` for the "Run tests" and "Lint (ruff)" tasks so a fresh
# checkout works without manual setup.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv"
VENV_PYTHON="$VENV/bin/python"
REQUIREMENTS="$REPO_ROOT/requirements-dev.txt"

if [ -x "$VENV_PYTHON" ]; then
    echo ".venv present, skipping setup."
    exit 0
fi

echo "Creating .venv (Python 3.12) at $VENV ..."
if ! command -v python3.12 >/dev/null 2>&1; then
    echo "ERROR: python3.12 not found on PATH. Install Python 3.12 first." >&2
    exit 1
fi
python3.12 -m venv "$VENV"

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r "$REQUIREMENTS"

echo "OK: .venv ready."
