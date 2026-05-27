# shellcheck shell=bash

ensure_this_file_sourced

case $- in
  *i*) ;;
  *) return 0 ;;
esac

# shellcheck source=/dev/null
. "$REMOTE_SHELL_DIR/welcome.lib.sh"

remote_ssh_welcome_main
