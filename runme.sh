#!/usr/bin/env bash

set -euo pipefail

# stdin comes from terminal, not from pipe or file
if [ -t 0 ]; then
  echo "NOTE: This script is intended to be run remotely (curl | bash)."
  exit 1
fi

REPO_URL="https://github.com/fmmaciej/remote-ssh.git"
INSTALL_DIR="${HOME}/.local/share/remote-ssh"
INSTALL_SCRIPT="install.sh"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required to install remote-ssh." >&2
  exit 127
fi

echo "[*] Cloning repo to: $INSTALL_DIR"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  echo "[*] Updating existing installation..."

  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "[*] Installing into $INSTALL_DIR..."

  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

echo "[*] Running install..."
(
  cd "$INSTALL_DIR"
  ./"$INSTALL_SCRIPT"
)
