# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_GENERATE_DEF_DIR:?TOOLS_GENERATE_DEF_DIR is not set (source tools/lib/env.sh first)}"

. "$TOOLS_COMMON_DIR/platform.sh"
. "$TOOLS_COMMON_DIR/github.sh"

. "$TOOLS_GENERATE_DEF_DIR/detect.sh"
. "$TOOLS_GENERATE_DEF_DIR/analyze.sh"
. "$TOOLS_GENERATE_DEF_DIR/render.sh"
