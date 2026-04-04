#!/usr/bin/env bash
# OpenSSH in WSL rejects private keys on /mnt/c (drvfs) when they appear mode 0777.
set -euo pipefail
unix_key="$1"
unix_repo="$2"
if [[ ! -f "$unix_key" ]]; then
  echo "Private key not found: $unix_key" >&2
  exit 1
fi
secure="${HOME}/.ssh/ha_deploy_mitsubishi_deploy"
mkdir -p "${HOME}/.ssh"
cp -f "$unix_key" "$secure"
chmod 600 "$secure"
export DEPLOY_HA_IDENTITY_WSL="$secure"
exec bash "${unix_repo}/scripts/deploy-ha-rsync.sh"
