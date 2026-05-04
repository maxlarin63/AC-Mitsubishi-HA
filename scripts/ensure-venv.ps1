# Ensure a working .venv (Python 3.12) at the repo root.
# - No-op if .venv\Scripts\python.exe already exists.
# - Otherwise: create the venv with `py -3.12 -m venv` and install requirements-dev.txt.
# Used as a `dependsOn` for the "Run tests" and "Lint (ruff)" tasks so a fresh
# checkout works without manual setup.

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $RepoRoot '.venv'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
$Requirements = Join-Path $RepoRoot 'requirements-dev.txt'

if (Test-Path $VenvPython) {
    Write-Host ".venv present, skipping setup."
    exit 0
}

Write-Host "Creating .venv (Python 3.12) at $Venv ..."
& py -3.12 -m venv $Venv
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create .venv with 'py -3.12 -m venv'. Is Python 3.12 installed and registered with the py launcher?"
    exit 1
}

& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $VenvPython -m pip install -r $Requirements
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "OK: .venv ready."
