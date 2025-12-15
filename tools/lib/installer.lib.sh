# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_INSTALLER_DIR:?TOOLS_INSTALLER_DIR is not set (source tools/lib/env.sh first)}"

# common/*
. "$TOOLS_COMMON_DIR/platform.sh"
. "$TOOLS_COMMON_DIR/mappings.sh"
. "$TOOLS_COMMON_DIR/assets.sh"
. "$TOOLS_COMMON_DIR/github.sh"
. "$TOOLS_COMMON_DIR/requirements.sh"
. "$TOOLS_COMMON_DIR/extract.sh"

# installer/*
. "$TOOLS_INSTALLER_DIR/defs.sh"
. "$TOOLS_INSTALLER_DIR/variants.sh"
. "$TOOLS_INSTALLER_DIR/version.sh"
. "$TOOLS_INSTALLER_DIR/download.sh"
. "$TOOLS_INSTALLER_DIR/install.sh"
. "$TOOLS_INSTALLER_DIR/main.sh"
