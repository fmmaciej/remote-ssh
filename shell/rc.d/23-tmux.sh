# shellcheck shell=sh

ensure_this_file_sourced

if have tmux; then
  tmuxrc() {
    if [ -f "$REMOTE_DOTS_DIR/tmux.conf" ]; then
      command tmux -f "$REMOTE_DOTS_DIR/tmux.conf" "$@"
    else
      command tmux "$@"
    fi
  }
fi
