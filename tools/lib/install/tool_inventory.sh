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

managed_tool_installed() {
  local tool="$1" link="$INSTALL_BIN_DIR/$1"

  [[ -x "$link" ]] || return 1
  remote_ssh_release_for_link "$link" "$tool" >/dev/null
}

managed_installed_tools() {
  local tool

  while IFS= read -r tool; do
    if managed_tool_installed "$tool"; then
      printf '%s\n' "$tool"
    fi
  done < <(all_known_tools)
}
