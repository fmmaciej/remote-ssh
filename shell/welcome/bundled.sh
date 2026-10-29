# shellcheck shell=bash

remote_ssh_welcome_render_remote_ssh() {
  remote_ssh_welcome_print_banner
  remote_ssh_welcome_print_host
  remote_ssh_welcome_print_update

  if remote_ssh_welcome_load_commands; then
    remote_ssh_welcome_print_tools
    remote_ssh_welcome_print_scripts
  else
    printf 'tools:   0 checked / 0 ok\n'
    printf 'scripts: 0 checked / 0 ok\n'
    remote_ssh_welcome_issue doctor
  fi
}

remote_ssh_welcome_render_hw() {
  remote_ssh_welcome_print_hw
}

remote_ssh_welcome_render_sw() {
  remote_ssh_welcome_print_sw
}

# This helper was loaded through welcome.lib.sh's absolute loader directory.
# Resolve its own source, independently of the caller's REMOTE_SHELL_DIR.
remote_ssh_welcome_bundled_shell_dir() {
  local __rs_wb_source="${BASH_SOURCE[0]%/*}"
  (builtin cd -P -- "$__rs_wb_source/.." && builtin pwd -P)
}

remote_ssh_welcome_bundled_renderer() {
  local __rs_wb_dir="$1" __rs_wb_path="$2" __rs_wb_renderer
  local __rs_wb_expected __rs_wb_actual='' __rs_wb_limit
  # The three wrappers deliberately share these exact bytes, including the LF.
  # shellcheck disable=SC2016
  local __rs_wb_prologue='#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/../welcome.lib.sh"

'

  if builtin test "$__rs_wb_path" = "$__rs_wb_dir/00-remote-ssh.sh"; then
    __rs_wb_renderer=remote_ssh_welcome_render_remote_ssh
  elif builtin test "$__rs_wb_path" = "$__rs_wb_dir/10-hw.sh"; then
    __rs_wb_renderer=remote_ssh_welcome_render_hw
  elif builtin test "$__rs_wb_path" = "$__rs_wb_dir/20-sw.sh"; then
    __rs_wb_renderer=remote_ssh_welcome_render_sw
  else
    return 1
  fi
  [[ -f "$__rs_wb_path" && -x "$__rs_wb_path" && ! -L "$__rs_wb_path" ]] || return 1

  __rs_wb_expected="$__rs_wb_prologue$__rs_wb_renderer"$'\n'
  __rs_wb_limit=$((${#__rs_wb_expected} + 1))
  # A NUL terminates read successfully, as does reaching the bounded limit.
  # Only EOF with exactly the canonical bytes qualifies; no command substitution
  # is used for the content, so final LF bytes are preserved on Bash 3.2 too.
  if LC_ALL=C IFS= builtin read -r -d '' -n "$__rs_wb_limit" __rs_wb_actual 2>/dev/null <"$__rs_wb_path"; then
    return 1
  fi
  builtin test "$__rs_wb_actual" = "$__rs_wb_expected" || return 1
  printf '%s\n' "$__rs_wb_renderer"
}

remote_ssh_welcome_bundled_options_unexported() {
  local __rs_wb_option __rs_wb_declaration __rs_wb_flags

  for __rs_wb_option in SHELLOPTS BASHOPTS; do
    if [ "$__rs_wb_option" = BASHOPTS ] && [[ -z "${BASHOPTS+x}" ]]; then
      continue
    fi
    __rs_wb_declaration="$(builtin declare -p "$__rs_wb_option" 2>/dev/null)" || return 1
    case "$__rs_wb_declaration" in
      'declare -'*) ;;
      *) return 1 ;;
    esac
    __rs_wb_flags="${__rs_wb_declaration#declare -}"
    __rs_wb_flags="${__rs_wb_flags%% *}"
    case "$__rs_wb_flags" in
      '' | *x*) return 1 ;;
    esac
  done
}

remote_ssh_welcome_bundled_render() {
  # Never dispatch a function name obtained from arbitrary file content.
  case "$1" in
    remote_ssh_welcome_render_remote_ssh) remote_ssh_welcome_render_remote_ssh ;;
    remote_ssh_welcome_render_hw) remote_ssh_welcome_render_hw ;;
    remote_ssh_welcome_render_sw) remote_ssh_welcome_render_sw ;;
    *) return 1 ;;
  esac
}
