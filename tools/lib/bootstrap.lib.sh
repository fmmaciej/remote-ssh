# shellcheck shell=bash

ensure_this_file_sourced

: "${TOOLS_COMMON_DIR:?TOOLS_COMMON_DIR is not set (source tools/lib/env.sh first)}"
: "${TOOLS_BOOTSTRAP_DIR:?TOOLS_BOOTSTRAP_DIR is not set (source tools/lib/env.sh first)}"

# shellcheck source=/dev/null
. "$TOOLS_COMMON_DIR/requirements.sh"

# shellcheck source=/dev/null
. "$TOOLS_BOOTSTRAP_DIR/requirements.sh"
# shellcheck source=/dev/null
. "$TOOLS_BOOTSTRAP_DIR/install.sh"
# shellcheck source=/dev/null
. "$TOOLS_BOOTSTRAP_DIR/dirs.sh"
# shellcheck source=/dev/null
. "$TOOLS_BOOTSTRAP_DIR/post_install.sh"
