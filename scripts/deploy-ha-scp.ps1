# deploy-ha-scp.ps1 — deploy custom_components\ac_mitsubishi to HA via SCP (no WSL).
# Reads credentials from .env.ha (git-ignored).

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$envFile = Join-Path $RepoRoot '.env.ha'
if (-not (Test-Path -LiteralPath $envFile)) {
    Write-Error @"
.env.ha not found at $envFile
Copy .env.ha.example to .env.ha and fill in values.
"@
    exit 1
}

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

$haHost = $env:HA_HOST
if (-not $haHost) {
    Write-Error 'HA_HOST not set in .env.ha'
    exit 1
}
$haUser = if ($env:HA_USER) { $env:HA_USER } else { 'root' }

$identity = $env:HA_SSH_IDENTITY
if (-not $identity) {
    $identity = Join-Path $env:USERPROFILE '.ssh\ha_deploy'
}

$manifestPath = Join-Path $RepoRoot 'custom_components\ac_mitsubishi\manifest.json'
$version = ''
if (Test-Path -LiteralPath $manifestPath) {
    try {
        $version = (Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json).version
    } catch {
        $version = ''
    }
}

$targetParent = '/config/custom_components/'
$destDisplay = "${haUser}@${haHost}:${targetParent}ac_mitsubishi/"
if ($version) {
    Write-Host "Deploying AC Mitsubishi v${version} to $destDisplay"
} else {
    Write-Host "Deploying AC Mitsubishi to $destDisplay"
}

$sshScpOpts = @('-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes')
$sshArgs = @($sshScpOpts)
$scpArgs = @($sshScpOpts)
if (Test-Path -LiteralPath $identity) {
    $sshArgs += @('-i', $identity)
    $scpArgs += @('-i', $identity)
}

$mkdirParent = $targetParent.TrimEnd('/')
$mkdirCmd = "mkdir -p `"$mkdirParent`""
& ssh @sshArgs "${haUser}@${haHost}" $mkdirCmd
if ($LASTEXITCODE -ne 0) {
    Write-Error "ssh failed (exit $LASTEXITCODE). Check HA_HOST, HA_USER, and HA_SSH_IDENTITY in .env.ha."
    exit $LASTEXITCODE
}

$src = Join-Path $RepoRoot 'custom_components\ac_mitsubishi'
$target = '{0}@{1}:{2}' -f $haUser, $haHost, $targetParent

$stageRoot = Join-Path $env:TEMP ('ha_scp_stage_' + [Guid]::NewGuid().ToString('N'))
$stagePkg = Join-Path $stageRoot 'ac_mitsubishi'
try {
    New-Item -ItemType Directory -Path $stagePkg -Force | Out-Null
    $null = robocopy $src $stagePkg /E `
        /XD __pycache__ .pytest_cache .mypy_cache .ruff_cache `
        /XF *.pyc `
        /NFL /NDL /NJH /NJS /NC /NS /NP
    $robocopyRc = $LASTEXITCODE
    if ($robocopyRc -ge 8) {
        Write-Error "Staging file copy failed (robocopy exit $robocopyRc)."
    }

    $scpArgs += @('-r', $stagePkg, $target)
    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Remove-Item -LiteralPath $stageRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host 'Deploy complete. (scp does not delete removed files on the host.)'

# Optional: restart Home Assistant Core via REST API (same as UI "Restart")
$haHttpUrl = $env:HA_HTTP_URL
$haToken = $env:HA_TOKEN
if ($haHttpUrl -and $haToken) {
    $haHttpUrl = $haHttpUrl.TrimEnd('/')
    $uri = "$haHttpUrl/api/services/homeassistant/restart"
    $headers = @{
        Authorization = "Bearer $haToken"
        'Content-Type' = 'application/json'
    }
    try {
        Write-Host "Restarting Home Assistant Core via $uri ..."
        # Use http:// on LAN if cert errors (Windows PowerShell 5.1 has no -SkipCertificateCheck).
        Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body '{}'
        Write-Host 'Restart requested. HA will be back in about a minute.'
    } catch {
        $httpCode = $null
        if ($_.Exception.Response) {
            $httpCode = [int]$_.Exception.Response.StatusCode
        }
        $msg = $_.Exception.Message
        # HA often tears down HTTP before the proxy finishes; 502/504 or connection reset is usually fine.
        $benign = ($httpCode -eq 504 -or $httpCode -eq 502) -or
            ($msg -match '504|502|Gateway Timeout|Bad Gateway|forcibly closed|Connection reset|underlying connection')
        if ($benign) {
            Write-Host 'Restart likely started (HA or proxy closed the request while restarting). Give it a minute.'
        } else {
            Write-Warning "Deploy succeeded but HA restart failed: $msg. Edit HA_HTTP_URL / HA_TOKEN in .env.ha or restart manually."
            exit 1
        }
    }
} elseif ($haHttpUrl -or $haToken) {
    Write-Warning 'Set both HA_HTTP_URL and HA_TOKEN in .env.ha for automatic restart after deploy (Profile -> Security -> Long-Lived Access Tokens).'
}
