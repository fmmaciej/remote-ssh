# shellcheck shell=bash

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_INSTALLER_DIR:?TOOLS_INSTALLER_DIR is not set (source tools/lib/env.sh first)}"

# common/*
# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/platform.sh"
# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/mappings.sh"
# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/assets.sh"
# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/github.sh"
# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/requirements.sh"
# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/extract.sh"

# installer/*
# shellcheck source=/dev/null
. "$TOOLS_INSTALLER_DIR/defs.sh"
# shellcheck source=/dev/null
. "$TOOLS_INSTALLER_DIR/variants.sh"
# shellcheck source=/dev/null
. "$TOOLS_INSTALLER_DIR/version.sh"
# shellcheck source=/dev/null
. "$TOOLS_INSTALLER_DIR/download.sh"
# shellcheck source=/dev/null
. "$TOOLS_INSTALLER_DIR/install.sh"
# shellcheck source=/dev/null
. "$TOOLS_INSTALLER_DIR/main.sh"
