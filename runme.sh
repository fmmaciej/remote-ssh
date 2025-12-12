#!/usr/bin/env bash

set -euo pipefail

REPO_URL="https://github.com/fmmaciej/remote-ssh.git"
INSTALL_DIR="${HOME}/.local/share/remote-ssh"
BOOTSTRAP_SCRIPT="bootstrap.sh"

echo "[*] Klonuję/aktualizuję repo do: $INSTALL_DIR"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" pull --ff-only
else
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

echo "[*] Uruchamiam bootstrap..."
(
  cd "$INSTALL_DIR"
  ./"$BOOTSTRAP_SCRIPT"
)
