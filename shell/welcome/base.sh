# shellcheck shell=bash

remote_ssh_welcome_lib_dir() {
  local script_path="${BASH_SOURCE[0]}"

  case "$script_path" in
    */*) script_path="${script_path%/*}/.." ;;
    *) script_path="." ;;
  esac
  cd -- "$script_path" && pwd
}

remote_ssh_welcome_repo_dir() {
  local script_dir

  script_dir="$(remote_ssh_welcome_lib_dir)"
  cd "$script_dir/.." && pwd
}

remote_ssh_welcome_bundled_dir() {
  if [[ -n "${REMOTE_SHELL_DIR:-}" ]]; then
    printf '%s/welcome.d\n' "$REMOTE_SHELL_DIR"
  else
    printf '%s/welcome.d\n' "$(remote_ssh_welcome_lib_dir)"
  fi
}

remote_ssh_welcome_bool_disabled() {
  case "${1:-}" in
    0 | false | no | off) return 0 ;;
    *) return 1 ;;
  esac
}

remote_ssh_welcome_trim() {
  local value="$1"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s\n' "$value"
}
