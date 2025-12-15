# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_GENERATOR_DIR:?TOOLS_GENERATOR_DIR is not set (source tools/lib/env.sh first)}"

. "$TOOLS_COMMON_DIR/platform.sh"
. "$TOOLS_COMMON_DIR/github.sh"

. "$TOOLS_GENERATOR_DIR/detect.sh"
. "$TOOLS_GENERATOR_DIR/guess.sh"
. "$TOOLS_GENERATOR_DIR/analyze.sh"
. "$TOOLS_GENERATOR_DIR/render.sh"
