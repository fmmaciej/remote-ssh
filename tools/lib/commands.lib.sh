# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMANDS_DIR:?TOOLS_COMMANDS_DIR is not set (source tools/lib/env.sh first)}"

remote_ssh_cmd_require_install_libs() {
  if [[ "${REMOTE_SSH_INSTALL_LIBS_LOADED:-0}" == "1" ]]; then
    return 0
  fi

  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/install.lib.sh"
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/install-tool.lib.sh"

  REMOTE_SSH_INSTALL_LIBS_LOADED=1
}

. "$TOOLS_COMMANDS_DIR/install.sh"
. "$TOOLS_COMMANDS_DIR/uninstall.sh"
. "$TOOLS_COMMANDS_DIR/tool.sh"
. "$TOOLS_COMMANDS_DIR/tool_status.sh"
. "$TOOLS_COMMANDS_DIR/check.sh"
. "$TOOLS_COMMANDS_DIR/update.sh"
. "$TOOLS_COMMANDS_DIR/git.sh"
. "$TOOLS_COMMANDS_DIR/doctor.sh"
. "$TOOLS_COMMANDS_DIR/prune.sh"
. "$TOOLS_COMMANDS_DIR/guide.sh"
. "$TOOLS_COMMANDS_DIR/help.sh"
