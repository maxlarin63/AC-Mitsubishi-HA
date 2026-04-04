$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$winForWsl = $RepoRoot.Replace('\', '/')

$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'SilentlyContinue'
$unixRoot = (wsl.exe wslpath '-u' $winForWsl).Trim()
$ErrorActionPreference = $prevEAP

if (-not $unixRoot -or $unixRoot -notmatch '^/') {
    Write-Error "Could not map repo path for WSL. Tried: $winForWsl (got: '$unixRoot'). Install a distro: wsl --install"
}

$winKey = Join-Path $env:USERPROFILE '.ssh\ha_deploy'
if (-not (Test-Path -LiteralPath $winKey)) {
    Write-Error "Private key not found: $winKey"
}

$ErrorActionPreference = 'SilentlyContinue'
$unixKey = (wsl.exe wslpath '-u' ($winKey.Replace('\', '/'))).Trim()
$ErrorActionPreference = $prevEAP

if ($unixKey -notmatch '^/') {
    Write-Error "Could not map key path for WSL: $winKey"
}

wsl.exe bash -lc "bash '$unixRoot/scripts/deploy-ha-wsl-bootstrap.sh' '$unixKey' '$unixRoot'"
