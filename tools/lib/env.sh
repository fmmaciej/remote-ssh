# shellcheck shell=bash
# shellcheck disable=SC2034
# shellcheck source=/dev/null

# remote-ssh/tools/lib
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# remote-ssh/
REPO_DIR="$SCRIPT_DIR/../.."

LIB_DIR="$REPO_DIR/lib"
. "$LIB_DIR/guards.sh"

ensure_this_file_sourced

BIN_DIR="$REPO_DIR/bin"
DOTS_DIR="$REPO_DIR/dots"
SHELL_DIR="$REPO_DIR/shell"
TOOLS_DIR="$REPO_DIR/tools"
TOOLS_LIB_DIR="$REPO_DIR/tools/lib"

TOOLS_COMMON_DIR="$TOOLS_LIB_DIR/common"
TOOLS_COMMANDS_DIR="$TOOLS_LIB_DIR/commands"
TOOLS_INSTALL_DIR="$TOOLS_LIB_DIR/install"
TOOLS_INSTALL_TOOL_DIR="$TOOLS_LIB_DIR/install-tool"
TOOLS_GENERATE_DEF_DIR="$TOOLS_LIB_DIR/generate-def"

# domyślne ścieżki instalacji (można nadpisać przed source)
: "${INSTALL_PREFIX:=${HOME}/.local/opt}"
: "${INSTALL_BIN_DIR:=${HOME}/.local/bin}"

. "$LIB_DIR/log.sh"
. "$LIB_DIR/helpers.sh"
