$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$envFile = Join-Path $RepoRoot '.env.ha'
if (Test-Path -LiteralPath $envFile) {
    Get-Content -LiteralPath $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }
        $eq = $line.IndexOf('=')
        if ($eq -lt 1) { return }
        $name = $line.Substring(0, $eq).Trim()
        $val = $line.Substring($eq + 1).Trim()
        if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        Set-Item -Path "Env:$name" -Value $val
    }
}

if (-not $env:HA_HOST -or -not $env:HA_USER) {
    Write-Error "Set HA_HOST and HA_USER in .env.ha (see .env.ha.example)."
}

$target = '{0}@{1}:/config/custom_components/ac_mitsubishi/' -f $env:HA_USER, $env:HA_HOST
$localDir = Join-Path $RepoRoot 'custom_components\ac_mitsubishi'

$identity = $env:HA_SSH_IDENTITY
if (-not $identity) {
    $identity = Join-Path $env:USERPROFILE '.ssh\ha_deploy'
}

$scpArgs = @()
if (Test-Path -LiteralPath $identity) {
    $scpArgs += @('-i', $identity)
}
$scpArgs += @('-r', $localDir, $target)

& scp @scpArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Deployed - restart HA (scp does not delete removed files on the host)'
