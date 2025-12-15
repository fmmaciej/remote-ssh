# shellcheck shell=bash

ensure_this_file_sourced

if have tmux; then
  tmux() {
    local conf_arg=()

    if [[ -f "$REMOTE_DOTS_DIR/tmux.conf" ]]; then
      conf_arg=(-f "$REMOTE_DOTS_DIR/tmux.conf")
    fi

    command tmux "${conf_arg[@]}" "$@"
  }
fi
