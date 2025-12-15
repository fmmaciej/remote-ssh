# shellcheck shell=bash

ensure_this_file_sourced

if have tmux; then
  [ -f "$REMOTE_DOTS_DIR/tmux.conf" ] && export TMUX_CONF="$REMOTE_DOTS_DIR/tmux.conf"
fi
