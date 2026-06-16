#!/usr/bin/env bash

set -euo pipefail

REPO_URL="https://github.com/fmmaciej/remote-ssh.git"
INSTALL_DIR="${HOME}/.local/share/remote-ssh"
REMOTE_SSH_REF="${REMOTE_SSH_REF:-}"

# First-install tool selection.
# Download this file, remove tools you do not want, then run: bash runme.sh
# Passing arguments overrides this list, e.g.: bash runme.sh fd rg fzf
# Any arguments are forwarded to remote-ssh install without interpretation.
RUNME_TOOLS=(
  fd
  rg
  sd
  dust
  fzf
  bat
  bottom
  procs
  yazi
  nvim
  zellij
  nu
  starship
  eza
  zoxide
  atuin
  navi
  bssh
)

refresh_checkout_from_upstream() {
  local repo_dir="$1"
  local upstream remote remote_branch untracked

  if ! upstream="$(git -C "$repo_dir" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)"; then
    echo "ERROR: No upstream branch is configured for $repo_dir." >&2
    return 1
  fi

  if [[ "$upstream" != */* ]]; then
    echo "ERROR: Unsupported upstream name: $upstream" >&2
    return 1
  fi

  remote="${upstream%%/*}"
  remote_branch="${upstream#*/}"

  echo "[*] Fetching $remote/$remote_branch"
  git -C "$repo_dir" fetch "$remote" "$remote_branch"

  echo "[*] Resetting tracked files to $upstream"
  git -C "$repo_dir" reset --hard "$upstream"

  untracked="$(git -C "$repo_dir" ls-files --others --exclude-standard 2>/dev/null || true)"
  if [[ -n "$untracked" ]]; then
    echo "[WARN] Untracked files were left in place:"
    printf '%s\n' "$untracked" | sed 's/^/  /'
  fi
}

install_args=()
if (($# > 0)); then
  install_args=("$@")
else
  install_args=("${RUNME_TOOLS[@]}")
fi

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required to install remote-ssh." >&2
  exit 127
fi

echo "[*] Cloning repo to: $INSTALL_DIR"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  if [[ -n "$REMOTE_SSH_REF" ]]; then
    echo "[*] Fetching remote-ssh ref: $REMOTE_SSH_REF"
    git -C "$INSTALL_DIR" fetch --depth 1 origin "$REMOTE_SSH_REF"
    git -C "$INSTALL_DIR" checkout --force --detach FETCH_HEAD
  else
    echo "[*] Updating existing installation..."
    refresh_checkout_from_upstream "$INSTALL_DIR"
  fi
else
  echo "[*] Installing into $INSTALL_DIR..."

  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
  if [[ -n "$REMOTE_SSH_REF" ]]; then
    echo "[*] Fetching remote-ssh ref: $REMOTE_SSH_REF"
    git -C "$INSTALL_DIR" fetch --depth 1 origin "$REMOTE_SSH_REF"
    git -C "$INSTALL_DIR" checkout --force --detach FETCH_HEAD
  fi
fi

echo "[*] Running install..."
(
  cd "$INSTALL_DIR"
  ./bin/remote-ssh install "${install_args[@]}"
)
