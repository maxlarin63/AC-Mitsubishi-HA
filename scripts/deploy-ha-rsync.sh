#!/usr/bin/env bash
# deploy-ha-rsync.sh — deploy custom_components/ac_mitsubishi to HA over SSH/rsync
# Reads credentials from .env.ha (git-ignored).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env.ha"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Copy .env.ha.example → .env.ha and fill in values." >&2
  exit 1
fi

# shellcheck source=/dev/null
set -a && source "$ENV_FILE" && set +a

# deploy-ha-wsl-bootstrap.sh / env: Windows key path in WSL after .env is loaded.
if [[ -n "${DEPLOY_HA_IDENTITY_WSL:-}" ]]; then
  HA_SSH_IDENTITY="$DEPLOY_HA_IDENTITY_WSL"
  export HA_SSH_IDENTITY
fi

HA_HOST="${HA_HOST:?HA_HOST not set in .env.ha}"
HA_USER="${HA_USER:-root}"
DEST="/config/custom_components/ac_mitsubishi"

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is not installed here (e.g. sudo apt install rsync)." >&2
  exit 1
fi

VERSION=""
MANIFEST="$REPO_ROOT/custom_components/ac_mitsubishi/manifest.json"
if [[ -f "$MANIFEST" ]]; then
  for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
      VERSION="$("$py" -c "import json; print(json.load(open('$MANIFEST'))['version'])" 2>/dev/null || true)"
      [[ -n "$VERSION" ]] && break
    fi
  done
fi

if [[ -n "$VERSION" ]]; then
  echo "→ Deploying AC Mitsubishi v${VERSION} to ${HA_USER}@${HA_HOST}:${DEST}/"
else
  echo "→ Deploying to ${HA_USER}@${HA_HOST}:${DEST}/"
fi

identity="${HA_SSH_IDENTITY:-}"
if [[ -z "$identity" && -f "$HOME/.ssh/ha_deploy" ]]; then
  identity="$HOME/.ssh/ha_deploy"
fi

SSH_OPTS=(-o StrictHostKeyChecking=no -o BatchMode=yes)
if [[ -n "$identity" && -f "$identity" ]]; then
  SSH_OPTS+=(-i "$identity")
fi
ssh_chk=(ssh "${SSH_OPTS[@]}")

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
  echo "Use the workspace task: Deploy to HA (scp from Windows; no rsync needed on the server)." >&2
  echo "Or install rsync on the server if you need the task: Deploy to HA (rsync via WSL)." >&2
  exit 1
fi

rsync -avz --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude '.mypy_cache/' \
  --exclude '.ruff_cache/' \
  -e "ssh ${SSH_OPTS[*]}" \
  "$REPO_ROOT/custom_components/ac_mitsubishi/" \
  "${HA_USER}@${HA_HOST}:${DEST}/"

echo "✓ Deploy complete."

# Optional: restart Home Assistant Core via REST API (same as UI "Restart")
if [[ -n "${HA_HTTP_URL:-}" && -n "${HA_TOKEN:-}" ]]; then
  if ! command -v curl >/dev/null 2>&1; then
    echo "HA_HTTP_URL / HA_TOKEN set but curl not found; restart HA manually." >&2
  else
    base="${HA_HTTP_URL%/}"
    uri="${base}/api/services/homeassistant/restart"
    echo "Restarting Home Assistant Core via REST API ..."
    set +e
    code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST \
      -H "Authorization: Bearer ${HA_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{}' \
      "$uri" 2>/dev/null)"
    rc=$?
    set -e
    if [[ "$rc" -ne 0 ]]; then
      echo "Restart likely started (HA closed the connection or network blip). Give it a minute."
    elif [[ "$code" == "200" || "$code" == "201" || "$code" == "204" ]]; then
      echo "Restart requested. HA will be back in about a minute."
    elif [[ "$code" == "502" || "$code" == "504" ]]; then
      echo "Restart likely started (HA or proxy returned ${code} while restarting). Give it a minute."
    else
      echo "Deploy succeeded but HA restart failed (HTTP ${code}). Edit HA_HTTP_URL / HA_TOKEN or restart manually." >&2
      exit 1
    fi
  fi
elif [[ -n "${HA_HTTP_URL:-}" || -n "${HA_TOKEN:-}" ]]; then
  echo "Set both HA_HTTP_URL and HA_TOKEN in .env.ha for automatic restart after deploy." >&2
fi
