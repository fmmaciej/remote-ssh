# shellcheck shell=bash

# remote-ssh/tools/lib
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# remote-ssh/
REPO_DIR="$SCRIPT_DIR/../.."

LIB_DIR="$REPO_DIR/lib"

# shellcheck source=/dev/null
. "$LIB_DIR/guards.sh"

ensure_this_file_sourced

# shellcheck disable=SC2034
BIN_DIR="$REPO_DIR/bin"
# shellcheck disable=SC2034
DOTS_DIR="$REPO_DIR/dots"
# shellcheck disable=SC2034
SHELL_DIR="$REPO_DIR/shell"
# shellcheck disable=SC2034
TOOLS_DIR="$REPO_DIR/tools"

TOOLS_LIB_DIR="$REPO_DIR/tools/lib"
# shellcheck disable=SC2034
TOOLS_COMMON_DIR="$TOOLS_LIB_DIR/common"
# shellcheck disable=SC2034
TOOLS_INSTALLER_DIR="$TOOLS_LIB_DIR/installer"
# shellcheck disable=SC2034
TOOLS_GENERATOR_DIR="$TOOLS_LIB_DIR/generator"
# shellcheck disable=SC2034
TOOLS_BOOTSTRAP_DIR="$TOOLS_LIB_DIR/bootstrap"

# domyślne ścieżki instalacji (można nadpisać przed source)
: "${INSTALL_PREFIX:=${HOME}/.local/opt}"
: "${INSTALL_BIN_DIR:=${HOME}/.local/bin}"

# shellcheck source=/dev/null
. "$LIB_DIR/log.sh"

# shellcheck source=/dev/null
. "$LIB_DIR/helpers.sh"
