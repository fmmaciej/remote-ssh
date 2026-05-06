# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_INSTALL_TOOL_DIR:?TOOLS_INSTALL_TOOL_DIR is not set (source tools/lib/env.sh first)}"

# common/*
. "$TOOLS_COMMON_DIR/platform.sh"
. "$TOOLS_COMMON_DIR/requirements.sh"
. "$TOOLS_COMMON_DIR/extract.sh"

# install-tool/*
. "$TOOLS_INSTALL_TOOL_DIR/defs.sh"
. "$TOOLS_INSTALL_TOOL_DIR/assets.sh"
. "$TOOLS_INSTALL_TOOL_DIR/download.sh"
. "$TOOLS_INSTALL_TOOL_DIR/install.sh"
. "$TOOLS_INSTALL_TOOL_DIR/main.sh"
