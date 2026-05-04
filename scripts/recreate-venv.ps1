# Delete .venv if present, then run ensure-venv.ps1 to rebuild it from scratch.
# Use after upgrading Python or when requirements-dev.txt changes.

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $RepoRoot '.venv'

if (Test-Path $Venv) {
    Write-Host "Removing existing .venv ..."
    Remove-Item -Recurse -Force $Venv
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'ensure-venv.ps1')
exit $LASTEXITCODE
