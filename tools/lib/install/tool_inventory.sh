# shellcheck shell=bash

ensure_this_file_sourced

known_tool() {
  local tool="$1"

  [[ -f "$TOOLS_DIR/defs/${tool}.sh" ]]
}

all_known_tools() {
  local def

  for def in "$TOOLS_DIR"/defs/*.sh; do
    [[ -f "$def" ]] || continue
    printf '%s\n' "${def##*/}" | sed 's/[.]sh$//'
  done
}

managed_installed_tools() {
  local tool target

  for tool in $(all_known_tools); do
    [[ -L "$INSTALL_BIN_DIR/$tool" ]] || continue
    target="$(readlink "$INSTALL_BIN_DIR/$tool")"
    case "$target" in
      "$INSTALL_PREFIX/${tool}-"*/*)
        printf '%s\n' "$tool"
        ;;
    esac
  done
}
