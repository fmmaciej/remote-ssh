#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

REMOTE_SHELL_DIR="$SCRIPT_DIR"

# shellcheck disable=SC1091
[ -f "$REMOTE_SHELL_DIR/env.sh" ] && . "$REMOTE_SHELL_DIR/env.sh"

# shellcheck disable=SC1091
[ -f "$REMOTE_SHELL_DIR/aliases.sh" ] && . "$REMOTE_SHELL_DIR/aliases.sh"

RC_D_DIR="$REMOTE_SHELL_DIR/rc.d"

if [ -d "$RC_D_DIR" ]; then
  # set nullglob, żeby nie dostać literalnego '*.sh' gdy katalog pusty
  shopt -s nullglob 2>/dev/null || true

  for f in "$RC_D_DIR"/*.sh; do
    [ -r "$f" ] || continue
    # shellcheck disable=SC1090
    . "$f"
  done

  # unset nullglob
  shopt -u nullglob 2>/dev/null || true
fi
