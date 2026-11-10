# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

# Private foundation; public lifecycle facades opt in after engine integration.
. "$TOOLS_COMMON_DIR/release.sh"
. "$TOOLS_INSTALL_TOOL_DIR/defs.sh"
. "$TOOLS_LIB_DIR/managed/state.sh"
. "$TOOLS_LIB_DIR/managed/inventory.sh"
. "$TOOLS_LIB_DIR/managed/lock.sh"
. "$TOOLS_LIB_DIR/managed/migration.sh"
. "$TOOLS_LIB_DIR/managed/journal.sh"
. "$TOOLS_LIB_DIR/managed/recovery.sh"

. "$TOOLS_LIB_DIR/managed/install.sh"

. "$TOOLS_LIB_DIR/managed/uninstall.sh"

. "$TOOLS_LIB_DIR/managed/update.sh"
