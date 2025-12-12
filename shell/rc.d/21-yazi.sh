# shellcheck shell=bash

ensure_this_file_sourced

if have yazi; then
  [ -d "$REMOTE_DOTS_DIR/yazi" ] && export YAZI_CONFIG_HOME="$REMOTE_DOTS_DIR/yazi"
fi
