#!/usr/bin/env bash
# Delete .venv if present, then run ensure-venv.sh to rebuild it from scratch.
# Use after upgrading Python or when requirements-dev.txt changes.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv"

if [ -d "$VENV" ]; then
    echo "Removing existing .venv ..."
    rm -rf "$VENV"
fi

bash "$(dirname "${BASH_SOURCE[0]}")/ensure-venv.sh"
