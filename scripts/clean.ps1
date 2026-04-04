$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $root 'custom_components'))) {
    Write-Error "Run from repo: scripts/clean.ps1 (unexpected root: $root)"
    exit 1
}
Set-Location $root

foreach ($name in @('.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', 'dist', 'build')) {
    $p = Join-Path $root $name
    if (Test-Path $p) {
        Remove-Item -Recurse -Force $p
        Write-Host "Removed $name"
    }
}

Remove-Item -Force (Join-Path $root '.coverage')

foreach ($sub in @('custom_components', 'tests', 'scripts')) {
    $base = Join-Path $root $sub
    if (-not (Test-Path $base)) { continue }
    Get-ChildItem -LiteralPath $base -Recurse -Directory -Filter '__pycache__' |
        ForEach-Object {
            Remove-Item -Recurse -Force $_.FullName
            Write-Host "Removed $($_.FullName)"
        }
}

foreach ($egg in (Get-ChildItem -LiteralPath $root -Directory -Filter '*.egg-info' -ErrorAction SilentlyContinue)) {
    Remove-Item -Recurse -Force $egg.FullName
    Write-Host "Removed $($egg.Name)"
}

foreach ($junk in @('Thumbs.db', '.DS_Store')) {
    $jp = Join-Path $root $junk
    if (Test-Path -LiteralPath $jp) { Remove-Item -Force -LiteralPath $jp }
}

Write-Host 'Clean finished.'
