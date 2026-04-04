#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f .env.ha ]]; then
  # shellcheck source=/dev/null
  set -a && . ./.env.ha && set +a
fi
# deploy-ha-wsl-bootstrap.sh / env: Windows key path in WSL after .env is loaded.
if [[ -n "${DEPLOY_HA_IDENTITY_WSL:-}" ]]; then
  HA_SSH_IDENTITY="$DEPLOY_HA_IDENTITY_WSL"
  export HA_SSH_IDENTITY
fi

if [[ -z "${HA_HOST:-}" ]] || [[ -z "${HA_USER:-}" ]]; then
  echo "Set HA_HOST and HA_USER in .env.ha (see .env.ha.example)." >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is not installed here (e.g. sudo apt install rsync)." >&2
  exit 1
fi

identity="${HA_SSH_IDENTITY:-}"
if [[ -z "$identity" && -f "$HOME/.ssh/ha_deploy" ]]; then
  identity="$HOME/.ssh/ha_deploy"
fi

opts=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new)
if [[ -n "$identity" && -f "$identity" ]]; then
  ssh_chk=(ssh -i "$identity" "${opts[@]}")
  export RSYNC_RSH="ssh -i ${identity} -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
else
  ssh_chk=(ssh "${opts[@]}")
  export RSYNC_RSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
fi

set +e
ssh_out="$("${ssh_chk[@]}" "${HA_USER}@${HA_HOST}" "command -v rsync >/dev/null 2>&1" 2>&1)"
ssh_rc=$?
set -e
if [[ "$ssh_rc" -ne 0 ]]; then
  if echo "$ssh_out" | grep -qiE 'Permission denied|Load key|bad permissions|UNPROTECTED PRIVATE KEY|ignored\.|keyboard-interactive'; then
    echo "SSH authentication failed (not a missing rsync on the server)." >&2
    echo "$ssh_out" >&2
    exit 1
  fi
  echo "SSH is OK, but this host has no rsync in PATH over SSH (typical on Home Assistant OS)." >&2
  echo "Use the workspace task: Deploy to HA  (scp from Windows; no rsync needed on the server)." >&2
  echo "Or install rsync on the server if you need the task: Deploy to HA (rsync via WSL)." >&2
  exit 1
fi

rsync -av --delete custom_components/ac_mitsubishi/ \
  "${HA_USER}@${HA_HOST}:/config/custom_components/ac_mitsubishi/"
echo "Deployed - restart HA"
