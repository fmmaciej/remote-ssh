# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

DEFAULT_TOOLS=(fd rg sd dust fzf bat yazi nvim zellij nu starship eza zoxide atuin navi tspin vector)

default_platform() {
  local plat raw_os raw_arch libc

  plat="$(detect_platform)"
  IFS='|' read -r raw_os raw_arch <<<"$plat"
  libc="$(detect_libc "$raw_os")"

  printf '%s:%s:%s\n' "$raw_os" "$raw_arch" "$libc"
}

default_tool_supported_on_platform() {
  local tool="$1" raw_os="$2" raw_arch="$3" libc="$4"
  local def_dir="$TOOLS_DIR/defs"

  load_defs "$def_dir" "$tool"
  select_asset "$raw_os" "$raw_arch" "$libc" "${ASSETS[@]}" >/dev/null
}

default_tools_for_platform() {
  local raw_os="$1" raw_arch="$2" libc="$3"
  local tool

  for tool in "${DEFAULT_TOOLS[@]}"; do
    if default_tool_supported_on_platform "$tool" "$raw_os" "$raw_arch" "$libc"; then
      printf '%s\n' "$tool"
    fi
  done
}

unsupported_default_tools_for_platform() {
  local raw_os="$1" raw_arch="$2" libc="$3"
  local tool

  for tool in "${DEFAULT_TOOLS[@]}"; do
    if ! default_tool_supported_on_platform "$tool" "$raw_os" "$raw_arch" "$libc"; then
      printf '%s\n' "$tool"
    fi
  done
}

current_default_tools() {
  local platform raw_os raw_arch libc

  platform="$(default_platform)"
  IFS=: read -r raw_os raw_arch libc <<<"$platform"
  default_tools_for_platform "$raw_os" "$raw_arch" "$libc"
}

current_unsupported_default_tools() {
  local platform raw_os raw_arch libc

  platform="$(default_platform)"
  IFS=: read -r raw_os raw_arch libc <<<"$platform"
  unsupported_default_tools_for_platform "$raw_os" "$raw_arch" "$libc"
}
