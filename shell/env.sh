# shellcheck shell=bash

# Ustawienia środowiska dla sesji remote-ssh.

# remote-ssh/shell/
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# remote-ssh/
REMOTE_ENV_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

REMOTE_BIN_DIR="$REMOTE_ENV_DIR/bin"
REMOTE_DOTS_DIR="$REMOTE_ENV_DIR/dots"
REMOTE_LIB_DIR="$REMOTE_ENV_DIR/lib"
REMOTE_SHELL_DIR="$REMOTE_ENV_DIR/shell"

export REMOTE_ENV_DIR REMOTE_BIN_DIR REMOTE_DOTS_DIR REMOTE_LIB_DIR REMOTE_SHELL_DIR

# shellcheck disable=SC1091
[ -f "$REMOTE_LIB_DIR/guards.sh" ] && . "$REMOTE_LIB_DIR/guards.sh"

# shellcheck disable=SC1091
[ -f "$REMOTE_LIB_DIR/helpers.sh" ] && . "$REMOTE_LIB_DIR/helpers.sh"

# Bootstrap wrzuca rzeczy tutaj
path_prepend "$HOME/.local/bin"

# Skrypty z repo (helpery do ssh, tmux, itp.)
path_prepend "$REMOTE_BIN_DIR"

export PATH
