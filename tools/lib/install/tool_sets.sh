# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

MINI_TOOLS=(rg fd sd)
QUICK_TOOLS=(rg fd sd bat starship eza zoxide navi atuin)
DEFAULT_TOOLS=(fd rg sd dust fzf bat yazi nvim zellij nu starship eza zoxide atuin navi tspin vector)
INSTALL_PROFILES=(mini quick full)

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
  install_profile_tools_for_platform full "$@"
}

unsupported_default_tools_for_platform() {
  unsupported_install_profile_tools_for_platform full "$@"
}

install_profile_known() {
  case "${1:-}" in
    mini|quick|full) return 0 ;;
    *) return 1 ;;
  esac
}

install_profile_tools() {
  local profile="${1:?profile required}"

  case "$profile" in
    mini) printf '%s\n' "${MINI_TOOLS[@]}" ;;
    quick) printf '%s\n' "${QUICK_TOOLS[@]}" ;;
    full) printf '%s\n' "${DEFAULT_TOOLS[@]}" ;;
    *) return 1 ;;
  esac
}

install_profile_tools_for_platform() {
  local profile="$1" raw_os="$2" raw_arch="$3" libc="$4"
  local tool

  while IFS= read -r tool; do
    if default_tool_supported_on_platform "$tool" "$raw_os" "$raw_arch" "$libc"; then
      printf '%s\n' "$tool"
    fi
  done < <(install_profile_tools "$profile")
}

unsupported_install_profile_tools_for_platform() {
  local profile="$1" raw_os="$2" raw_arch="$3" libc="$4"
  local tool

  while IFS= read -r tool; do
    if ! default_tool_supported_on_platform "$tool" "$raw_os" "$raw_arch" "$libc"; then
      printf '%s\n' "$tool"
    fi
  done < <(install_profile_tools "$profile")
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

current_install_profile_tools() {
  local profile="$1"
  local platform raw_os raw_arch libc

  platform="$(default_platform)"
  IFS=: read -r raw_os raw_arch libc <<<"$platform"
  install_profile_tools_for_platform "$profile" "$raw_os" "$raw_arch" "$libc"
}

current_unsupported_install_profile_tools() {
  local profile="$1"
  local platform raw_os raw_arch libc

  platform="$(default_platform)"
  IFS=: read -r raw_os raw_arch libc <<<"$platform"
  unsupported_install_profile_tools_for_platform "$profile" "$raw_os" "$raw_arch" "$libc"
}

filter_tools_for_current_platform() {
  local platform raw_os raw_arch libc tool

  REMOTE_SSH_SUPPORTED_TOOLS=()
  REMOTE_SSH_UNSUPPORTED_TOOLS=()
  REMOTE_SSH_UNKNOWN_TOOLS=()

  platform="$(default_platform)"
  IFS=: read -r raw_os raw_arch libc <<<"$platform"

  for tool in "$@"; do
    if ! known_tool "$tool"; then
      REMOTE_SSH_UNKNOWN_TOOLS+=("$tool")
    elif default_tool_supported_on_platform "$tool" "$raw_os" "$raw_arch" "$libc"; then
      REMOTE_SSH_SUPPORTED_TOOLS+=("$tool")
    else
      REMOTE_SSH_UNSUPPORTED_TOOLS+=("$tool")
    fi
  done
}

read_expected_tools_for_current_platform() {
  local tool
  local -a configured=()

  REMOTE_SSH_EXPECTED_TOOLS=()
  REMOTE_SSH_UNSUPPORTED_TOOLS=()
  REMOTE_SSH_UNKNOWN_TOOLS=()

  expected_tools_exists || return 1

  while IFS= read -r tool; do
    [[ -n "$tool" ]] && configured+=("$tool")
  done < <(read_expected_tools)

  filter_tools_for_current_platform "${configured[@]}"
  REMOTE_SSH_EXPECTED_TOOLS=("${REMOTE_SSH_SUPPORTED_TOOLS[@]}")
  return 0
}
