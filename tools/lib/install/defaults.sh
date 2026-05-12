# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_INSTALL_DIR:?TOOLS_INSTALL_DIR is not set (source tools/lib/env.sh first)}"

. "$TOOLS_INSTALL_DIR/expected_tools.sh"
. "$TOOLS_INSTALL_DIR/tool_inventory.sh"
. "$TOOLS_INSTALL_DIR/tool_sets.sh"
