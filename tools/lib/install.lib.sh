# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_INSTALL_DIR:?TOOLS_INSTALL_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_INSTALL_TOOL_DIR:?TOOLS_INSTALL_TOOL_DIR is not set (source tools/lib/env.sh first)}"

# common/
. "$TOOLS_COMMON_DIR/requirements.sh"

# install/
. "$TOOLS_INSTALL_DIR/defaults.sh"
. "$TOOLS_INSTALL_DIR/requirements.sh"
. "$TOOLS_INSTALL_TOOL_DIR/defs.sh"
. "$TOOLS_INSTALL_DIR/install.sh"
. "$TOOLS_INSTALL_DIR/dirs.sh"
. "$TOOLS_INSTALL_DIR/post_install.sh"
