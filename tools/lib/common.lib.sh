# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"

# common/*
. "$TOOLS_COMMON_DIR/platform.sh"
. "$TOOLS_COMMON_DIR/mappings.sh"
. "$TOOLS_COMMON_DIR/assets.sh"
. "$TOOLS_COMMON_DIR/github.sh"
. "$TOOLS_COMMON_DIR/requirements.sh"
. "$TOOLS_COMMON_DIR/extract.sh"
