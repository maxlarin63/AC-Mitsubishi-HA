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

# Parent only: scp -r ./ac_mitsubishi user@host:.../custom_components/ -> .../custom_components/ac_mitsubishi/
# A target ending in .../ac_mitsubishi/ would nest to .../ac_mitsubishi/ac_mitsubishi/.
$target = '{0}@{1}:/config/custom_components/' -f $env:HA_USER, $env:HA_HOST
$src = Join-Path $RepoRoot 'custom_components\ac_mitsubishi'

$identity = $env:HA_SSH_IDENTITY
if (-not $identity) {
    $identity = Join-Path $env:USERPROFILE '.ssh\ha_deploy'
}

$stageRoot = Join-Path $env:TEMP ('ha_scp_stage_' + [Guid]::NewGuid().ToString('N'))
$stagePkg = Join-Path $stageRoot 'ac_mitsubishi'
try {
    New-Item -ItemType Directory -Path $stagePkg -Force | Out-Null
    # Skip bytecode and caches (scp has no --exclude).
    $null = robocopy $src $stagePkg /E `
        /XD __pycache__ .pytest_cache .mypy_cache .ruff_cache `
        /XF *.pyc `
        /NFL /NDL /NJH /NJS /NC /NS /NP
    $robocopyRc = $LASTEXITCODE
    if ($robocopyRc -ge 8) {
        Write-Error "Staging file copy failed (robocopy exit $robocopyRc)."
    }

    $scpArgs = @()
    if (Test-Path -LiteralPath $identity) {
        $scpArgs += @('-i', $identity)
    }
    $scpArgs += @('-r', $stagePkg, $target)

    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Remove-Item -LiteralPath $stageRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host 'Deployed - restart HA (scp does not delete removed files on the host)'
