# shellcheck shell=bash

ensure_this_file_sourced

# generator korzysta z:
# - TOOLS_COMMON_DIR, TOOLS_GENERATOR_DIR (ustawione w tools/lib/env.sh)

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_GENERATOR_DIR:?TOOLS_GENERATOR_DIR is not set (source tools/lib/env.sh first)}"

# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/platform.sh"
# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/github.sh"

# shellcheck source=/dev/null
. "$TOOLS_GENERATOR_DIR/detect.sh"
# shellcheck source=/dev/null
. "$TOOLS_GENERATOR_DIR/guess.sh"
# shellcheck source=/dev/null
. "$TOOLS_GENERATOR_DIR/analyze.sh"
# shellcheck source=/dev/null
. "$TOOLS_GENERATOR_DIR/render.sh"
