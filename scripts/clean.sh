#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
rm -f .coverage

for sub in custom_components tests scripts; do
  [[ -d "$sub" ]] || continue
  find "$sub" -type d -name '__pycache__' 2>/dev/null | while IFS= read -r p; do
    rm -rf "$p"
  done
done

shopt -s nullglob
for e in ./*.egg-info; do
  rm -rf "$e"
done
shopt -u nullglob

rm -f Thumbs.db .DS_Store

echo "Clean finished."
