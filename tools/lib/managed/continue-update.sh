#!/usr/bin/env bash
# Private same-PID update continuation. Not a public CLI or a staging bypass.
set -euo pipefail

(($# >= 5)) || exit 1
INSTALL_PREFIX="$1" INSTALL_BIN_DIR="$2"
export INSTALL_PREFIX INSTALL_BIN_DIR
SCRIPT_DIR="$(cd -P -- "${BASH_SOURCE[0]%/*}" && pwd -P)" || exit 1
# shellcheck source=/dev/null
. "$SCRIPT_DIR/../env.sh"
# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/commands.lib.sh"
remote_ssh_cmd_require_managed_libs
ms_continue_update_run "$@"
