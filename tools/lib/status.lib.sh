# shellcheck shell=bash
# shellcheck source=/dev/null

# Minimal status surface for login-time welcome checks.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

. "$SCRIPT_DIR/env.sh"

ensure_this_file_sourced

if [[ "${REMOTE_SSH_STATUS_LIB_LOADED:-0}" == "1" ]]; then
  return 0
fi

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_INSTALL_DIR:?TOOLS_INSTALL_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_INSTALL_TOOL_DIR:?TOOLS_INSTALL_TOOL_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_COMMANDS_DIR:?TOOLS_COMMANDS_DIR is not set (source tools/lib/env.sh first)}"

. "$TOOLS_COMMON_DIR/platform.sh"
. "$TOOLS_INSTALL_TOOL_DIR/defs.sh"
. "$TOOLS_INSTALL_TOOL_DIR/assets.sh"
. "$TOOLS_INSTALL_DIR/expected_tools.sh"
. "$TOOLS_INSTALL_DIR/tool_inventory.sh"
. "$TOOLS_INSTALL_DIR/tool_sets.sh"
. "$TOOLS_COMMANDS_DIR/tool_status.sh"
. "$TOOLS_COMMANDS_DIR/scripts.sh"

REMOTE_SSH_STATUS_LIB_LOADED=1
