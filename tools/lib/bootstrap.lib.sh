# shellcheck shell=bash
# shellcheck source=/dev/null

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_BOOTSTRAP_DIR:?TOOLS_BOOTSTRAP_DIR is not set (source tools/lib/env.sh first)}"

. "$TOOLS_COMMON_DIR/requirements.sh"

. "$TOOLS_BOOTSTRAP_DIR/requirements.sh"
. "$TOOLS_BOOTSTRAP_DIR/install.sh"
. "$TOOLS_BOOTSTRAP_DIR/dirs.sh"
. "$TOOLS_BOOTSTRAP_DIR/post_install.sh"
